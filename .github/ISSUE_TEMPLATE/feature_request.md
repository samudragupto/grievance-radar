name: Feature request
description: Suggest an idea or enhancement for Grievance Radar
labels: ["enhancement"]
body:
  - type: textarea
    id: feature-description
    attributes:
      label: Feature proposal
      description: What capability would you like to see added?
    validations:
      required: true
  - type: textarea
    id: motivation
    attributes:
      label: Motivation / Use Case
      description: How does this help municipal officers or administrators?
    validations:
      required: false
