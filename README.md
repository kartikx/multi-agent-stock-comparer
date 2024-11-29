# Multi Agent Stock Comparer
This is an implementation for a stock comparer using [AutoGen](https://github.com/microsoft/autogen/tree/main).

There are two agents:
1. Assistant: Takes the user prompt, writes the script, and interprets any errors in code execution.
2. Executor: Executes scripts in a docker container, installing packages if necessary.

This code is heavily inspired from the [quick start](https://microsoft.github.io/autogen/0.4.0.dev2//user-guide/core-user-guide/quickstart.html).

## Run it yourself!
To run this yourself, you'll need an OpenAI API key. One invocation of the program should cost less than 1c.

```sh
export OPENAI_API_KEY="<your key>"
```

You'll also need to install autogen packages from pip.
```sh
pip install autogen-core==0.4.0.dev2 autogen-ext==0.4.0.dev2
```