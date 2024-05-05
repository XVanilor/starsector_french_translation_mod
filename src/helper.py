import shutil
from abc import ABC, abstractmethod
import argparse
import csv
import json
from pathlib import Path
import os

# Récupérer le chemin absolu de la racine du mod
mod_path = os.getcwd()
starsector_data_dir = os.path.abspath(os.path.join(mod_path, "../../starsector-core/data"))

# Charger la configuration des fichiers de traductions disponibles
config_fp = open(os.path.join(mod_path, "src/config.json"))
config = json.load(config_fp)
config_fp.close()

data_dir = os.path.join(mod_path, 'data')
translations_dir = os.path.join(mod_path, "translations")


class Parsable(ABC):

    file: str

    _data_file_path: Path
    _translation_file_path: Path

    def __init__(self, file_path: str):

        self.file = file_path
        self._data_file_path = Path(os.path.join(data_dir, self.file))
        self._translation_file_path = Path(os.path.join(translations_dir, self.file))

    @abstractmethod
    def extract_translatable_content(self) -> str:
        pass

    @abstractmethod
    def write_translations_to_data(self) -> None:
        pass

    @abstractmethod
    def get_columns(self) -> set[str]:
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

    def get_path(self) -> str:
        return self.file

    def get_translation_file_path(self) -> Path:
        return self._translation_file_path

    def get_data_file_path(self) -> Path:
        return self._data_file_path


class TranslatableString:

    file: str
    id: str
    original_string: str

    def __init__(self, file: str, id: str, original_string) -> None:
        self.file = file
        self.id = id
        self.original_string = original_string

    # Optimisation trick to calculate set() more efficiently
    def __hash__(self):
        super().__hash__(self.file+"-"+self.id)

    def to_csv_line(self):

        # On encapsule la chaîne de caractères originale dans des " pour la lire plus facilement en CSV
        formatted_data = '"'+self.original_string.replace('"', '\\"')+'"'

        return "{},{},{}\n".format(self.id, formatted_data, "")


class TranslationFile:

    strings: set[TranslatableString]


class CsvFile(Parsable):
    
    key_columns: set[str]
    translatable_fields: set[str]

    def __init__(self, file, key_columns, translatable_fields) -> None:
        super().__init__(file)
        self.key_columns = key_columns
        self.translatable_fields = translatable_fields
    
    def get_columns(self) -> set[str]:
        return self.translatable_fields

    def get_id(self) -> str:
        return ".".join(self.key_columns)

    def extract_translatable_content(self) -> list[TranslatableString]:

        translations = []

        with open(self.get_data_file_path(), "r", encoding="utf-8") as fp:

            reader = csv.reader(fp)
            # Récupérer le header CSV
            header = reader.__next__()

            # Retrouver les indexes numériques des champs servant d'ID
            id_indexes = [header.index(i) for i in self.key_columns if i in header]
            # Retrouver les indexes numériques des champs traduisibles
            translatable_indexes = [header.index(i) for i in self.translatable_fields if i in header]

            for row in reader:

                for i in translatable_indexes:
                    column_name = header[i]
                    translatable_string = row[i]
                    id_value = "{}.{}".format(".".join(row[i] for i in id_indexes), column_name)

                    translations.append(TranslatableString(self.file, id_value, translatable_string))

        return translations

    def write_translations_to_data(self):

        with open(self.get_translation_file_path(), "r", encoding="utf-8") as fp:
            pass


class JsonFile(Parsable):

    translatable_fields: set[str]

    def get_id(self) -> str:
        raise NotImplementedError()

    def get_columns(self) -> set[str]:
        return self.translatable_fields


class TextFile(Parsable):

    content: str


# TODO Diff tool to retrieve modified translatable files

def fetch_game_translations(src_file: Parsable):

    src_file_path = os.path.join(starsector_data_dir, src_file.get_path())

    data_file_path = src_file.get_data_file_path()
    translation_file_path = src_file.get_translation_file_path()

    print(f"Traitement de '{src_file_path}' et écriture dans '{data_file_path}'")

    if not os.path.exists(src_file_path):
        print(f"Erreur: Le fichier source spécifié n'existe pas")
        return

    # Créer l'arborescence dans le fichier de data avec les traductions originales
    data_file_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_file_path, data_file_path)

    # Créer l'arborescence dans le dossier de traductions
    translation_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Extraire du contenu des champs traduisibles
    print("Extraction des chaînes à traduire...")
    trans_data = src_file.extract_translatable_content()

    # Les chaînes de caractères à traduire ont toutes été extraites du fichier source, on les écrit dans un fichier formatté
    with open(translation_file_path, "w") as fp:

        print(f"Écriture des chaînes à traduire dans {translation_file_path}")

        # On écrit le header CSV du fichier
        fp.write("id_do_not_translate_this,original_text,translation\n")

        # On écrit les données à traduire
        for translatable_string in trans_data:
            fp.write(translatable_string.to_csv_line())


def update_data_with_new_translations(src_file: Parsable):
    pass


def main():
    parser = argparse.ArgumentParser(description='Copier et traiter des fichiers .csv pour la traduction de Starsector.')
    # Commented: For now, the root folder is always ../../starsector-core/data
    # parser.add_argument('--root', required=True, help="Le chemin vers le dossier de StarSector")
    subparser = parser.add_subparsers(help="Subcommand command help", dest="command")
    subparser.add_parser("fetch", help="Fetch command help")
    subparser.add_parser("write", help="Write command help")

    args = parser.parse_args()

    for file_type in config["translatable_files"].keys():

        for parsing_attrs in config["translatable_files"][file_type]:
            if file_type == "csv":
                src_file = CsvFile(**parsing_attrs)
            elif file_type == "json":
                #print("Les fichiers JSON ne sont pas (encore) supportés")
                continue
                # src_file = JsonFile(**parsing_attrs)
            elif file_type == "txt":
                #print("Les fichiers textes ne sont pas (encore) supportés")
                continue
                # src_file = TextFile()
            else:
                raise ValueError("L'extension de fichier {} n'est pas supportée".format(file_type))

            if args.command == "fetch":
                fetch_game_translations(src_file)
            elif args.command == 'write':
                update_data_with_new_translations(src_file)


if __name__ == "__main__":
    main()
