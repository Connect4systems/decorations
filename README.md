### Decorations

App for small decoration company

### Project costs

Set a Company on each Project, an Account on each Cost Type, and a default
account for that company in each Mode of Payment. Amounts use the company currency.
Users posting costs need permission to create and submit Journal Entries and create Files.

Save a Cost as a draft, then submit it to automatically create a submitted Journal
Entry. The entry debits the Cost Type account and credits the Mode of Payment
account, with the project on both rows and the company's default cost center.
The Cost reference and note appear in the journal remarks; attachments are linked
to the journal with their privacy preserved. A confirmation includes the journal
link, which is also saved on the Cost. Cancelling the Cost cancels its journal;
the user must have Journal Entry cancellation permission.

After updating the app, run `bench --site <site> migrate` to apply the Cost fields.
Run controller tests with `bench --site <site> run-tests --app decorations --doctype Cost`.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app decorations
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/decorations
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
