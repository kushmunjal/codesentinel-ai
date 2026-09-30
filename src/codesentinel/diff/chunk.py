import tiktoken

def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def chunk_diff(filtered_diff: str, max_tokens: int = 2000, model_name: str = "gpt-4") -> list[str]:
    # Simple chunker: chunks file by file. If a file is too large, it might need line-level chunking
    # but for v1 we just chunk by file blocks.
    files = []
    current_file_lines = []
    
    for line in filtered_diff.split("\n"):
        if line.startswith("diff --git "):
            if current_file_lines:
                files.append("\n".join(current_file_lines))
                current_file_lines = []
        current_file_lines.append(line)
    
    if current_file_lines:
        files.append("\n".join(current_file_lines))
        
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for f in files:
        f_tokens = count_tokens(f, model_name)
        if current_tokens + f_tokens > max_tokens and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0
            
        current_chunk.append(f)
        current_tokens += f_tokens
        
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks
