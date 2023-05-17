#!/usr/bin/python3
import atheris
import sys

with atheris.instrument_imports():
    from prance import ResolvingParser

def RandomString(fdp, min_len, max_len):
  str_len = fdp.ConsumeIntInRange(min_len, max_len)
  return fdp.ConsumeUnicodeNoSurrogates(str_len)

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)

    str = RandomString(fdp, 0, 100)

    try:
        ResolvingParser(str)
    except AssertionError:
        pass
    except RuntimeError:
        pass
    except ValueError:
        pass

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()