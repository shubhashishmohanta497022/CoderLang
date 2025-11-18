import os
import logging

log = logging.getLogger(__name__)

class FileTool:
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Reads the content of a file.
        """
        log.info(f"Attempting to read file: {file_path}")
        try:
            if not os.path.exists(file_path):
                log.warning(f"File not found: {file_path}")
                return f"Error: File {file_path} does not exist."
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            log.info(f"Successfully read {len(content)} bytes from {file_path}")
            return content
        except Exception as e:
            log.error(f"Failed to read file: {e}")
            return f"Error reading file: {e}"

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """
        Writes content to a file. Creates directories if they don't exist.
        """
        log.info(f"Attempting to write to file: {file_path}")
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
                log.info(f"Created directory: {directory}")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            log.info(f"Successfully wrote to {file_path}")
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            log.error(f"Failed to write file: {e}")
            return f"Error writing file: {e}"

    @staticmethod
    def list_files(directory: str = ".") -> str:
        """
        Lists all files in a directory.
        """
        log.info(f"Listing files in: {directory}")
        try:
            if not os.path.exists(directory):
                return f"Error: Directory {directory} does not exist."
                
            files = os.listdir(directory)
            return "\n".join(files)
        except Exception as e:
            log.error(f"Failed to list files: {e}")
            return f"Error listing files: {e}"