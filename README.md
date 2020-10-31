# RASA Chatbot

## Requirements

> Any compatible version for **Pandas**
> 0.12.3 for **Rasa NLU**
> 0.10.1 for **Rasa Core**

Check `requirements.txt` for complete information

We use prebuild models provided by Spacy for intent classification and entity extraction
```
pip install rasa_nlu[spacy]
python -m spacy download en_core_web_md
python -m spacy link en_core_web_md en
```

## Configs and Keys

Zomato api key `config` and Gmail external app password `password` are provided as global variables in `actions.py`. The key and the password provided will be deactivated after marks are published.

## To Run

Construct the NLU model,
`python nlu_model.py`
To train online,
`python train_online.py`
To run on cmd line,
`python dialogue_management_model.py`

## Versions

> ### v0.1
> 
> ##### Intent and Entity Extraction:
> - common examples
>   - Simple statement parsing, i.e statements with single entity
> - regex expression
>   - greet
> - synomyms
>   - tier1 cities, their alternate names and misspellings
> ##### Stories
> - Knitting a story for the available intents and entities
> ##### Actions
> - Placeholder for checking locations, zomato api and sending email


> ### v0.2
> 
> ##### Intent and Entity Extraction:
> - common examples
>   - two entity statements
> - regex expression
>   - enriched greet regex
>   - location regex with common suffixes
> ##### Stories
> - Stories for the two entity statements
> ##### Actions
> - Zomato api access and parsing result to a dataframe

> ### v0.3
> 
> ##### Intent and Entity Extraction:
> - common examples
>   - added synonymous words as entities in on and two entity statements
> - regex expression
>   - budget variable regex as feature
>   - email id regex
> - synonyms
>   - for budget words
>   - for cuisine words with misspellings
> ##### Stories
> - Stories around sending email
> ##### Actions
> - Email sending api

> ### v0.4
> 
> ##### Intent and Entity Extraction:
> - common examples
>   - more examples with locations
> - regex expression
>   - better budget regex exp for all possible occurance
> - synonyms
>   - more statements using synonyms to increase accuracy
> ##### Stories
> - Stories around checking location
> ##### Actions
> - Action for checking and handling unknown locations