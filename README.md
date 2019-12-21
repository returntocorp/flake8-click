# flake8-click

Flake8 plugin for detecting [Click](https://click.palletsprojects.com/en/7.x/) best practices, by [r2c](https://r2c.dev). Available by default alongside other great tools in [Bento](https://bento.dev).

## Checks

- `r2c-click-option-function-argument-check`: missing a matching function argument for options defined with `click.option`
- `r2c-click-names-are-well-formed`: checks for
  - click option name does not begin with '-'
  - click argument name begins with '-'
  - click parameter is missing name
- `r2c-click-launch-uses-literal`: `click.launch` may be called with user input, leading to a security
  vulnerability

## Installing

```console
$ pip install flake8-click
```

_Specify `python2` or `python3` to install for a specific Python version._

And double check that it was installed correctly:

```console
$ flake8 --version
3.7.9 (flake8-click: 0.2.5, mccabe: 0.6.1, pycodestyle: 2.5.0, pyflakes: 2.1.1)
```

## Usage

```console
$ flake8 --select=r2c-click /path/to/code
```