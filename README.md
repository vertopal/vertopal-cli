# Vertopal-CLI

**Vertopal-CLI** is a small yet powerful utility that allows you to convert
digital files into various formats using the
[Vertopal public API](https://www.vertopal.com/en/developer/api).

You can use Vertopal-CLI by either *terminal commands* or
*importing as a Python package*.

## Installing Vertopal-CLI

Vertopal-CLI is available on [PyPI](https://pypi.org/project/vertopal/):

```bash
python -m pip install vertopal
```

You can also download the most recent version of Vertopal-CLI binaries for
**macOS**, **Windows**, and **Linux** from the
[releases page](https://github.com/vertopal/vertopal-cli/releases/latest) or
the [product page](https://www.vertopal.com/en/product/cli).

### Installer

An automatic installer is available for each different platform. It will run an
install script that downloads and copy Vertopal-CLI binaries to the correct
location.

Using macOS Terminal:

```bash
curl https://run.vertopal.com/cli/macos | bash
```

On Windows using PowerShell:

```bash
(curl https://run.vertopal.com/cli/windows).Content | iex
```

If you are getting any **UnauthorizedAccess** error, then start Windows
PowerShell with the "Run as administrator" option and run
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine`.
Now re-run the above installation command. To change the
[*Execution Policies*](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies)
to its default, you can run
`Set-ExecutionPolicy -ExecutionPolicy Default -Scope LocalMachine`.

Using Linux Terminal:

```bash
curl https://run.vertopal.com/cli/linux | bash
```

## Using Vertopal-CLI

To use Vertopal-CLI you need to [obtain an App-ID and a Security Token](http://www.vertopal.com/en/account/api/app/new).

Converting files using terminal commands are very simple:

```bash
vertopal convert document.ipynb --to pdf
```

To view full command-line help, execute `vertopal --help`
and `vertopal convert --help` in terminal.

### Setting App ID and Security Token

Before executing `vertopal convert` commands in terminal, you need to set
your obtained App-ID and Security Token in global configuration file:

```bash
vertopal config --app "your-app-id" --token "your-security-token"
```

### Importing as Python package

Importing vertopal as a Python package makes it easy
to implement file conversions in your projects.

The following code illustrates
[GIF to APNG](https://www.vertopal.com/en/convert/gif-to-apng) conversion using
the Vertopal Python package.

```python
import vertopal

converter = vertopal.Converter(
    "MickeyMouse.gif",
    app="your-app-id",
    token="your-security-token",
)
converter.convert("apng")
converter.wait()
if converter.is_converted():
    converter.download()
```
