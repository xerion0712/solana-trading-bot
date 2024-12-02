from pathlib import Path

from invoke import Context, task, Collection, Program

ROOT = Path(__file__).parent.resolve()


@task
def fix_venv(c: Context) -> None:
    """Fix package imports inside venv"""
    path = (
        ROOT
        / "venv/lib/python3.10/site-packages/telegram/vendor/ptb_urllib3/urllib3/_collections.py"
    )
    text = path.read_text()
    text = text.replace(
        "from collections import Mapping, MutableMapping",
        "from collections.abc import Mapping, MutableMapping",
    )

    path = (
        ROOT
        / "venv/lib/python3.10/site-packages/telegram/vendor/ptb_urllib3/urllib3/util/selectors.py"
    )
    text = path.read_text()
    text = text.replace(
        "from collections import namedtuple, Mapping",
        "from collections import namedtuple\nfrom collections.abc import Mapping",
    )
    print("venv was fixed")


def main() -> None:
    ns = Collection("solbot")
    tasks = [
        fix_venv,
    ]
    for task_ in tasks:
        ns.add_task(task_)
    Program(namespace=ns).run()


if __name__ == "__main__":
    main()
