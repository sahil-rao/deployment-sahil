# health-check

This performs a series of health checks to check that the dbsilos are in a
healthy state.  In order to use it, first do:

```shell
% make
```

Which will build a Python virtual environment that contains all of the Python
libraries necessary to run the tests.  Afterwards, you can now run the test
itself:

```shell
% ./venv/bin/health-check --bastion navopt-alpha alpha us-west-1 dbsilo4
   Executing checklist:  NavOpt Cluster Health Checklist
   1 checks to execute in the checklist:

      Executing checklist:  DBSILO4 Health Checklist
      1 checks to execute in the checklist:
...
```
