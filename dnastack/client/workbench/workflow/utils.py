import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple, Optional


class LoadedFile:

    def __init__(self, abs_location: Path, rel_location: Path, content: bytes):
        self.abs_location = abs_location
        self.rel_location = rel_location
        self.content = content


class WorkflowSourceLoaderError(Exception):
    pass


class WorkflowSourceLoader(object):
    def __init__(self, entrypoint=None, source_files: List[Path]=None):
        if not source_files:
            raise WorkflowSourceLoaderError("Cannot load workflow source files. At least one file must be specified")
        self.source_files = source_files
        self._entrypoint = entrypoint
        self._load_files()

    def _resolve_content(self, uri: Optional[Path], path: Path, _visited: List[Path]) -> List[Tuple[Path, bytes]]:
        cwd = Path.cwd().resolve()
        try:
            if not uri:
                import_path = path.resolve()
            else:
                os.chdir(uri)
                import_path = Path(os.path.join(uri, path)).resolve()

            if not import_path.exists():
                raise IOError(
                    f"Could not open file {import_path}. Caller does not have permission or it does not not exist or is")

            if import_path not in _visited:
                _visited.append(import_path)
            else:
                return []

            resolved_content = []
            all_imported_contents = []
            if path.name.endswith(".wdl"):
                pattern = re.compile(r'^\s*import\s["\'](?!http)(.+)["\'].*$')
                with import_path.open('r') as fp:
                    content = ""
                    for line in fp.readlines():
                        content += line
                        match = pattern.match(line)
                        if match:
                            import_statement = Path(match.group(1))
                            imported_contents = self._resolve_content(import_path.parent, import_statement, _visited)
                            all_imported_contents.extend(imported_contents)
                    resolved_content.append((import_path, content.encode()))
                    resolved_content.extend(all_imported_contents)
            else:
                with import_path.open('rb') as fp:
                    resolved_content.append((import_path, fp.read()))
            return resolved_content
        finally:
            os.chdir(cwd)

    def _load_files(self):
        path_and_contents: List[Tuple[Path, bytes]] = []
        _visited = []
        for path in self.source_files:
            path_and_contents.extend(self._resolve_content(None, Path(path), _visited))
        wdl_files = [wdl_file for wdl_file in path_and_contents if wdl_file[0].name.endswith(".wdl")]
        if len(wdl_files) == 0:
            raise ValueError("No WDL files defined")

        # Add the parent of the primary path
        # Given the list of absolute paths, strip the common leading path off of the set of paths
        # and the relativize each file path to the common leading path

        if len(path_and_contents) > 1:
            common_path = Path(os.path.commonpath([file[0] for file in path_and_contents] + [Path(os.path.abspath(self.entrypoint))]))
            self._loaded_files: List[LoadedFile] = [
                    LoadedFile(file[0], Path(file[0]).relative_to(common_path), file[1]) for file in path_and_contents]

            self._entrypoint = Path(os.path.abspath(self.entrypoint)).relative_to(common_path)
        else:
            self._entrypoint = Path(os.path.basename(self.entrypoint))
            self._loaded_files = [LoadedFile(file[0], Path(file[0].name), file[1]) for file in path_and_contents]


    def to_zip(self) -> Path:
        tempdir = tempfile.mkdtemp()
        output_location = os.path.join(tempdir, 'dependencies.zip')
        with zipfile.ZipFile(output_location,'w') as output_zip:
            for file in self.loaded_files:
                file_loc = os.path.join(tempdir, file.rel_location)
                dir_name = os.path.dirname(file_loc)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                with open(file_loc, 'wb') as f:
                    f.write(file.content)
                output_zip.write(file_loc, arcname=Path(file_loc).relative_to(tempdir))
        return Path(output_location)

    @property
    def loaded_files(self) -> List[LoadedFile]:
        return self._loaded_files

    @property
    def entrypoint(self) -> str:
        return str(self._entrypoint)


