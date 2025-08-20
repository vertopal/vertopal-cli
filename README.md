# Vertopal CLI

Vertopal CLI is a small yet powerful utility that allows you to convert digital files into various formats using the [Vertopal public API](https://www.vertopal.com/en/developer/api).

You can use Vertopal CLI by either *terminal commands* or *importing as a Python package*.

## Installing Vertopal CLI

Vertopal CLI is available on [PyPI](https://pypi.org/project/vertopal/):

```bash
python -m pip install vertopal
```

You can also download the most recent version of Vertopal CLI binaries for **macOS**, **Windows**, and **Linux** from the [releases page](https://github.com/vertopal/vertopal-cli/releases/latest) or the [product page](https://www.vertopal.com/en/product/cli).

### Installer

An automatic installer is available for each different platform. It will run an install script that downloads and copy Vertopal CLI binaries to the correct location.

Using macOS Terminal:

```bash
curl https://run.vertopal.com/cli/macos | bash
```

On Windows using PowerShell:

```bash
(curl https://run.vertopal.com/cli/windows).Content | iex
```

> [!TIP]
> If you are getting any `UnauthorizedAccess` error, then start Windows PowerShell with the "Run as administrator" option and run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine`.
>
> Now rerun the above installation command. To change the [*Execution Policies*](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies) to its default, you can run `Set-ExecutionPolicy -ExecutionPolicy Default -Scope LocalMachine`.

Using Linux Terminal:

```bash
curl https://run.vertopal.com/cli/linux | bash
```

## Using Vertopal CLI

Starting with **Vertopal CLI v2.0** the package ships with a public default credential (app: `free`, token: `FREE-TOKEN`) so you can try the CLI and Python client without creating an account. This default credential is suitable for personal testing and evaluation and is subject to daily rate limits; if you intend to run production workloads or to exceed the free limits, [obtain a private Application ID and Security Token](http://www.vertopal.com/en/account/api/app/new) from your Vertopal account and configure them (see the [configuration section](#setting-app-id-and-security-token-optional)).

Converting files from the terminal is simple:

```bash
vertopal convert report.pdf --to docx
```

### Bulk Conversion Support

Vertopal CLI supports **bulk conversion**, allowing you to process multiple files, entire directories, or complex patterns in a single command. You can combine:

- Brace expansion: `{a,b}`, `{1..5}`
- Bracket expansion: `[abc]`, `[0-9]`
- Wildcards: `*`, `?`
- Recursive globs: `**/*`
- Exclusion filters: `--exclude` for fine‑grained control
- Date filtering: `--modified-since` for time‑based selection

Here are some real‑world examples:

```bash
# Convert quarterly reports for multiple years
vertopal convert report_{2022,2023,2024}_{Q1,Q2,Q3,Q4}.pdf --to txt

# Convert files in multiple folders with different extensions
vertopal convert ./{docs,src,tests}/**/*.{txt,md,pdf} --to html

# Convert numbered chapters with exclusions
vertopal convert chapter_{01..20}.docx --exclude "chapter_{05,10,15}.docx" --to txt

# Convert all PDFs recursively, excluding drafts and backups
vertopal convert ./**/*.pdf --exclude "*draft*" "*backup*" --to txt

# Convert only files modified since a given date
vertopal convert **/*.docx --modified-since 2025-01-01 --to pdf
```

For the complete pattern syntax and advanced usage scenarios, see the [Enhanced Pattern Matching Guide](docs/cli/patterns.md).

### Streaming Conversions (stdin/stdout)

Vertopal CLI can also read from standard input and write to standard output, making
it easy to integrate into pipelines or generate files on the fly without intermediate
storage.

```bash
# Create a PDF from Markdown text provided via stdin
echo "Vertopal is **AWESOME!**" | vertopal convert - --from md --to pdf --output awesome.pdf
```

### Setting App ID and Security Token (optional)

If you have a private Application ID and Security Token (recommended for production), configure them in the user configuration file.

Set credentials using the `vertopal config` subcommand:

```bash
vertopal config api.app "your-app-id" api.token "your-security-token"
```

After setting a private credential, the CLI and Python client will use it for authenticated requests. If you do not set credentials, the bundled public credential will be used by default.

### Importing as Python package

Importing vertopal as a Python package makes it easy to implement file conversions in your projects.

The following code illustrates [GIF to APNG](https://www.vertopal.com/en/convert/gif-to-apng) conversion using the Vertopal Python package.

```python
from vertopal import Converter
from vertopal.io import FileInput, FileOutput

source = FileInput("./MickeyMouse.gif")
sink = FileOutput("./MickeyMouse.apng")

converter = Converter()
conversion = converter.convert(
    readable=source,
    writable=sink,
    output_format="apng",
)
conversion.wait()
if conversion.successful():
    conversion.download()
```
