# Commure Takehome Assessment

## Description

This project parses HL7 messages and converts them into JSON format.

## Usage

Run the parser using Python:

```bash
python3 parser.py <input_file_name.hl7>
```

## Docker usage

Run Docker :
```
docker pull addlurum/hl7parser

docker run --rm -v $(pwd):/app addlurum/hl7parser <input_file_name.hl7>
```
