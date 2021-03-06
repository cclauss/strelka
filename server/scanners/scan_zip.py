import io
import zipfile
import zlib

from server import objects


class ScanZip(objects.StrelkaScanner):
    """Extracts files from ZIP archives.

    Options:
        limit: Maximum number of files to extract.
            Defaults to 1000.
    """
    def scan(self, file_object, options):
        file_limit = options.get("limit", 1000)

        self.metadata["total"] = {"files": 0, "extracted": 0}

        with io.BytesIO(file_object.data) as zip_object:
            try:
                with zipfile.ZipFile(zip_object) as zip_file_:
                    name_list = zip_file_.namelist()
                    self.metadata["total"]["files"] = len(name_list)
                    for name in name_list:
                        if not name.endswith("/"):
                            if self.metadata["total"]["extracted"] >= file_limit:
                                break

                            try:
                                child_file = zip_file_.read(name)
                                child_filename = f"{self.scanner_name}::{name}"
                                child_fo = objects.StrelkaFile(data=child_file,
                                                               filename=child_filename,
                                                               depth=file_object.depth + 1,
                                                               parent_uid=file_object.uid,
                                                               root_uid=file_object.root_uid,
                                                               parent_hash=file_object.hash,
                                                               root_hash=file_object.root_hash,
                                                               source=self.scanner_name)
                                self.children.append(child_fo)
                                self.metadata["total"]["extracted"] += 1

                            except NotImplementedError:
                                file_object.flags.append(f"{self.scanner_name}::unsupported_compression")
                            except RuntimeError:
                                file_object.flags.append(f"{self.scanner_name}::runtime_error")
                            except ValueError:
                                file_object.flags.append(f"{self.scanner_name}::value_error")
                            except zlib.error:
                                file_object.flags.append(f"{self.scanner_name}::zlib_error")

            except zipfile.BadZipFile:
                file_object.flags.append(f"{self.scanner_name}::bad_zip_file")
