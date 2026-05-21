import difflib

class DiffDetector:
    @staticmethod
    def has_changes(old_content, new_content):
        
        if old_content is None:
            return True

        return old_content.strip() != new_content.strip()

    @staticmethod
    def get_changes(old_content, new_content):
        
        if old_content is None:
            return "Это первый снапшот страницы."

        diff = difflib.unified_diff(old_content.splitlines(), new_content.splitlines(), lineterm="")

        changes = []

        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                changes.append(line)

        if not changes:
            return "Существенных изменений не найдено."

        return "\n".join(changes[:20])