# CLERK
Community Library of Executable Reasoning Kits

## Reasoning Kit Structure
The abstract overview of a reasoning kit.

```
{
    "resources": {
        "1": {
            "content": "Full text",
            "link": "",
            "resource_id": "resource_1"
        },
        "2": {
            "content": "",
            "link": "https://blob-storage.cloud-provider.com/file.pdf",
            "resource_id": "resource_2"
        }
    }
    "workflow": {
        "1": {
            "type": "instruction",
            "prompt": "Look at this document:\n{resource_1}\nand classify it",
            "evaluation": "",
            "output_id": "workflow_1"
        },
        "2": {
            "type": "instruction",
            "prompt": "Look up a definition for this classification:\n{workflow_1}\nfrom this resource:\n{resource_2}",
            "evalaution": "",
            "output_id": "workflow_2"
        },
        "3": {
            "type": "instruction",
            "prompt": "Generate the final answer with this context information:\n{resource_1}\n{workflow_1}\n{workflow_2}",
            "evaluation": "",
            "output_id": "workflow_3"
        }
    }
}
```

## Workflow
The workflow runs chronologically. I.e., start with the first item in workflow. Import all necessary resources referenced in workflow_1. Then go one etc. See general tasks for more details.

## General Tasks
- [ ] Let user define resources and workflow from terminal
- [ ] Langchain logic, which executes all steps from the workflow
- [ ] For evaluation steps, interrupt logic and ask for user feedback
- [ ] After final event, present all results back to user
- [ ] Wrap this in FastAPI

## Tasks (to be implemented another time)
- [ ] change reasoning_kits/demo/resource_1.txt to pdf and add pdf support for resources.
