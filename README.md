# click-linter

Flake8 plugin for detecting click best practices

## Checks

- CLC001: checks for missing help text for `click.option`-s
- CLC100: missing argument for `click.option`
- CLC101: click option name does not begin with '-'
- CLC102: click argument name begins with '-'
- CLC103: click parameter is missing name
- CLC200: `click.launch` may be called with user input, leading to a security
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
