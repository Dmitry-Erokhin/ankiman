## Preparation

To verify that everything is working porperly:
1. activate venv (`source .venv/bin/activate`)
2. install ankiman (`poetry install`)
3. execute ankiman with corresponding commands

## Commands

### process-text
Use deck "DE"
Use tag "ankiman-test"

for instance:

```sh
ankiman process-text -d "DE" -t ankiman-test Schlecht
```

If you need to test several words, do in in "one go":

```sh
ankiman process-text -d "DE" -t ankiman-test "Schlecht, Gut, Bett"
```
