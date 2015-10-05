#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click

from .sample_dump import Samples

@click.group()
@click.pass_context
def main(ctx):
    """
    """
    pass

@main.command()
def scratch():
    """"""

    sampler = Samples()

