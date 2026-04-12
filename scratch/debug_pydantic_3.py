import sys
print("Importing spacy...")
try:
    import spacy
    print("spacy imported")
except Exception as e:
    import traceback
    traceback.print_exc()

print("\nImporting spellchecker...")
try:
    from spellchecker import SpellChecker
    print("spellchecker imported")
except Exception as e:
    import traceback
    traceback.print_exc()
