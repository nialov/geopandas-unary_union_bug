"""
nox sessions.
"""
import nox


@nox.session(python=["3.7.1", "3.8", "3.9"], reuse_venv=True)
def test(session):
    """
    Nox session for all py versions.
    """
    session.install("poetry")
    session.run("poetry", "install")
    session.run("poetry", "run", "pytest")
