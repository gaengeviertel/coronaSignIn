import os

from invoke import task


@task
def tdd(c):
    os.remove(".testmondata")
    c.run("ptw --clear -- --testmon", pty=True)


@task
def test(c):
    c.run("pytest")


@task
def containertests(c):
    c.run("pytest tests_container")
