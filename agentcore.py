from autogen_ext.models import OpenAIChatCompletionClient
from autogen_ext.code_executors import DockerCommandLineCodeExecutor
from autogen_core.application import SingleThreadedAgentRuntime
import tempfile
from dataclasses import dataclass
from typing import List
import os
import asyncio

from autogen_core.base import MessageContext
from autogen_core.components import DefaultTopicId, RoutedAgent, default_subscription, message_handler
from autogen_core.components.code_executor import CodeExecutor, extract_markdown_code_blocks, CodeBlock
from autogen_core.components.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    SystemMessage,
    UserMessage,
)
from autogen_core.base import CancellationToken


@dataclass
class Message:
    content: str


@default_subscription
class Assistant(RoutedAgent):
    def __init__(self, model_client: ChatCompletionClient) -> None:
        super().__init__("An assistant agent.")
        self._model_client = model_client
        self._chat_history: List[LLMMessage] = [
            SystemMessage(
                content="""Write Python script in markdown block, and it will be executed.
Always save figures to file in the current directory. Do not use plt.show(). Do not ask to execute or open any python files."""
                # Package installations should be using bash scripts with pip.""",
            )
        ]

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        print("Topic: ", ctx.topic_id)

        self._chat_history.append(UserMessage(
            content=message.content, source="user"))
        result = await self._model_client.create(self._chat_history)
        print(f"\n{'-'*80}\nAssistant:\n{result.content}")
        self._chat_history.append(AssistantMessage(
            content=result.content, source="assistant"))  # type: ignore
        # type: ignore
        await self.publish_message(Message(content=result.content), DefaultTopicId())


@default_subscription
class Executor(RoutedAgent):
    def __init__(self, code_executor: CodeExecutor) -> None:
        super().__init__("An executor agent.")
        self._code_executor = code_executor

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        code_blocks = extract_markdown_code_blocks(message.content)
        if code_blocks:
            print("Executing: ", code_blocks)
            result = await self._code_executor.execute_code_blocks(
                code_blocks, cancellation_token=ctx.cancellation_token
            )
            # Does result indicate completion?
            print(f"\n{'-'*80}\nExecutor:\n{result.output}")

            message = f"""Executed code:\n{message.content}\n{
                '-'*20}\nReceived result:\n{result.output}"""

            await self.publish_message(Message(content=message), DefaultTopicId())
            print("Sent message")


work_dir = tempfile.mkdtemp()

# Create an local embedded runtime.
runtime = SingleThreadedAgentRuntime()


async def main():
    # type: ignore[syntax]
    async with DockerCommandLineCodeExecutor(work_dir=work_dir) as executor:
        # Register the assistant and executor agents by providing
        # their agent types, the factory functions for creating instance and subscriptions.

        await Assistant.register(
            runtime,
            "assistant",
            lambda: Assistant(
                OpenAIChatCompletionClient(
                    model="gpt-4o-mini",
                    api_key=os.environ["OPENAI_KEY"]
                )
            ),
        )

        await Executor.register(runtime, "executor", lambda: Executor(executor))

        # Start the runtime and publish a message to the assistant.
        runtime.start()

        input_text = input(">> ")
        message_content = f"""{
            input_text}. Compare returns of these stocks on a single plot from 2024-01-01 to YTD"""

        await runtime.publish_message(
            Message(message_content), DefaultTopicId()
        )

        await runtime.stop_when_idle()

if __name__ == '__main__':
    asyncio.run(main())
