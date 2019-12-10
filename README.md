# click-linter

Flake8 plugin for detecting click best practices

## Checks

- `r2c-click-option-function-argument-check`: missing argument for `click.option`
- `r2c-click-names-are-well-formed`: checks for
  - click option name does not begin with '-'
  - click argument name begins with '-'
  - click parameter is missing name
- `r2c-click-launch-uses-literal`: `click.launch` may be called with user input, leading to a security
  vulnerability

## Installing

```
$ python -m pip install flake8-click
```

_Specify `python2` or `python3` to install for a specific Python version._

And double check that it was installed correctly:

```
$ python -m flake8 -h
Usage: flake8 [options] file file ...

...

Installed plugins: flake8-click : 0.1.0, mccabe: 0.5.3, pycodestyle: 2.2.0, pyflakes: 1.3.0
```

Note the `flake8-click: 0.1.0`.

## Using

Click best practices is a flake8 plugin. You can easily use this plugin by

```
$ python -m flake8 --select=CLC /path/to/code
```

## Testing

```
$ pytest
```
