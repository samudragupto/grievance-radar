name: Bug report
description: Create a report to help us improve Grievance Radar
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for filing a bug report.
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Describe what bug or anomaly occurred.
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: What commands or actions trigger this behavior?
    validations:
      required: true
  - type: input
    id: environment
    attributes:
      label: Environment
      description: OS version, Python version, dependencies.
    validations:
      required: false
