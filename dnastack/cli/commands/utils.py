from dnastack.cli.core.command_spec import ArgumentSpec

MAX_RESULTS_ARG = ArgumentSpec(
    name="max_results",
    arg_names=["--max-results"],
    help="Limit the total number of results.",
    type=int,
)

PAGINATION_PAGE_ARG = ArgumentSpec(
    name="page",
    arg_names=["--page"],
    help="Set the page number. This allows for jumping into an arbitrary page of results. Zero-based.",
    type=int,
)

PAGINATION_PAGE_SIZE_ARG = ArgumentSpec(
    name="page_size",
    arg_names=["--page-size"],
    help="Set the page size returned by the server.",
    type=int,
)
