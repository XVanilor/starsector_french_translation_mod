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


class TranslationFile:

    file: Path
    translation_map: dict

    def __init__(self, file_path: Path):
        self.file = file_path
        self.translation_map = {}

    def load(self) -> dict:

        self.translation_map = {}
        if not self.file.exists():
            return self.translation_map

        with open(self.file, "r") as fp:
            reader = csv.reader(fp)
            # Passer le header
            reader.__next__()

            for row in reader:
                string_id = row[0]
                original_str = row[1]
                translated_str = row[2]

                self.translation_map[string_id] = (original_str, translated_str)

        return self.translation_map

    def update_from_dict(self, new_translation_dict: dict):

        new_trans_map = dict(new_translation_dict, **self.translation_map)
        self.translation_map = new_trans_map
        return self.translation_map

    def write(self):

        with open(self.file, "w") as fp:
            writer = csv.writer(fp)
            # Écrire le header
            writer.writerow(["id_do_not_translate", "original_text", "translation"])

            for string_id in self.translation_map:
                content = self.translation_map[string_id]
                if content[0] == "":
                    continue
                writer.writerow([string_id, content[0], content[1]])


class Parsable(ABC):

    file: str

    _data_file_path: Path
    _translation_file_path: Path

    def __init__(self, file_path: str):

        self.file = file_path
        self._data_file_path = Path(os.path.join(data_dir, self.file))
        self._translation_file_path = Path(os.path.join(translations_dir, self.file))

    @abstractmethod
    def extract_translatable_content(self) -> dict:
        pass

    @abstractmethod
    def rewrite_data_file(self, inf, outf, translation_map: dict):
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

    def __get_translatable_column_ids(self, csv_header: list[str]) -> list[int]:
        return [csv_header.index(i) for i in self.translatable_fields if i in csv_header]

    @staticmethod
    def __get_row_id(csv_ids_index: list[int], row: list[str]) -> str:
        return ".".join(row[i] for i in csv_ids_index)

    @staticmethod
    def __get_string_id(row_id: str, column_name: str) -> str:
        return "{}.{}".format(row_id, column_name)

    def extract_translatable_content(self) -> dict:

        translations = {}

        with open(self.get_data_file_path(), "r", encoding="utf-8") as fp:

            reader = csv.reader(fp)
            # Récupérer le header CSV
            header = reader.__next__()

            # Retrouver les indexes numériques des champs servant d'ID
            id_indexes = [header.index(i) for i in self.key_columns if i in header]
            # Retrouver les indexes numériques des champs traduisibles
            translatable_indexes = self.__get_translatable_column_ids(header)

            for row in reader:
                for i in translatable_indexes:
                    column_name = header[i]
                    translatable_string = row[i]

                    string_id = self.__get_string_id(self.__get_row_id(id_indexes, row), column_name)
                    translations[string_id] = (translatable_string, "")

        return translations

    def rewrite_data_file(self, fp_r, fp_w, translation_map: dict):

        # Remplacement dans le fichier data des chaînes de caractères traduites
        reader = csv.reader(fp_r)
        writer = csv.writer(fp_w)

        # Passer le header
        header = reader.__next__()
        writer.writerow(header)

        # Retrouver les indexes numériques des champs servant d'ID
        id_indexes = [header.index(i) for i in self.key_columns if i in header]
        # Retrouver les indexes numériques des champs traduisibles
        translatable_indexes = self.__get_translatable_column_ids(header)

        for row in reader:
            for i in translatable_indexes:
                column_name = header[i]
                string_id = self.__get_string_id(self.__get_row_id(id_indexes, row), column_name)

                # Remplacer l'ancienne chaîne par celle traduite
                if string_id in translation_map:
                    row[i] = translation_map[string_id]

            writer.writerow(row)

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

    # Les chaînes de caractères à traduire ont toutes été extraites du fichier source
    # On les écrit dans un fichier formaté
    print(f"Écriture des chaînes à traduire dans {translation_file_path}")

    translation_file = TranslationFile(translation_file_path)
    translation_file.load()
    translation_file.update_from_dict(trans_data)
    translation_file.write()


def write_translations_to_data_file(src_file: Parsable):

    translation_file = TranslationFile(src_file.get_translation_file_path())
    translation_file.load()

    translation_map = dict(map(lambda kv: (kv[0], kv[1][1] if kv[1][1] != "" else kv[1][0]),
                               translation_file.translation_map.items()))

    # Réécrire du fichier présent dans data
    original_file = src_file.get_data_file_path()
    tmp_file = str(src_file.get_data_file_path())+".tmp"
    with open(original_file) as inf, open(tmp_file, 'w') as outf:
        src_file.rewrite_data_file(inf, outf, translation_map)
    os.remove(original_file)
    os.rename(tmp_file, original_file)


def main():
    parser = argparse.ArgumentParser(description='Copier et traiter des fichiers de texte pour la traduction de Starsector.')
    subparser = parser.add_subparsers(dest="command")
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
                raise ValueError(f"L'extension de fichier {file_type} n'est pas supportée")

            if args.command == "fetch":
                fetch_game_translations(src_file)
            elif args.command == 'write':
                write_translations_to_data_file(src_file)


if __name__ == "__main__":
    main()
