# Maps a file line number to the position in the unified diff patch
# so GitHub can attach the comment correctly.

def map_line_to_position(patch: str, target_line: int) -> int:
    # A minimal implementation. 
    # position is the 1-based line number in the patch.
    # We must track the new file line number.
    
    lines = patch.split('\n')
    current_new_line = -1
    
    for position, line in enumerate(lines, start=1):
        if line.startswith("@@"):
            # @@ -12,4 +12,5 @@ 
            # Extract new file start line
            parts = line.split(" ")
            new_file_range = parts[2] # e.g. +12,5 or +12
            new_start = int(new_file_range.split(",")[0].replace("+", ""))
            current_new_line = new_start
        elif line.startswith("+") and not line.startswith("+++"):
            if current_new_line == target_line:
                return position
            current_new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            # deleted lines don't advance the new file line number
            pass
        else:
            if current_new_line == target_line:
                return position
            current_new_line += 1
            
    return -1
