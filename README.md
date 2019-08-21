# click-linter

Flake8 plugin for detecting click best practices

## Checks

- CLC001: checks for missing help text for `click.option`-s

## Installing

```
$ python -m pip install click_best_practices
```

_Specify `python2` or `python3` to install for a specific Python version._

And double check that it was installed correctly:

```
$ python -m flake8 -h
Usage: flake8 [options] file file ...

...

Installed plugins: click_best_practices: 0.1.0, mccabe: 0.5.3, pycodestyle: 2.2.0, pyflakes: 1.3.0
```

Note the `click_best_practices: 0.1.0`.

## Using

Click best practices is a flake8 plugin. You can easily use this plugin by

```
$ python -m flake8 --select=CLC /path/to/code
```

## Testing

```
$ pytest
```
