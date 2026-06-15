import json
import os
import sys

def convert():
    transcript_path = "/home/tkogut/.gemini/antigravity-cli/brain/6035a5e8-c308-47b3-a07d-2c63648b618b/.system_generated/logs/transcript_full.jsonl"
    output_path = "tmp/conversation_history.md"
    
    if not os.path.exists(transcript_path):
        print(f"Error: Transcript not found at {transcript_path}")
        return

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# 💬 Historia Rozmowy - Automatyzacja Google Workflow z n8n\n\n")
        out.write("Ta historia została automatycznie wygenerowana z logów systemowych Antigravity.\n\n---\n\n")
        
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    source = step.get("source", "")
                    step_type = step.get("type", "")
                    content = step.get("content", "")
                    created_at = step.get("created_at", "")
                    
                    # Formatting timestamp
                    time_str = created_at.split("T")[-1].split("Z")[0][:8] if created_at else ""
                    
                    if step_type == "USER_INPUT":
                        # Strip USER_REQUEST tags if present
                        clean_content = content.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
                        # Also strip metadata
                        if "<ADDITIONAL_METADATA>" in clean_content:
                            clean_content = clean_content.split("<ADDITIONAL_METADATA>")[0].strip()
                        
                        out.write(f"### 👤 Użytkownik ({time_str})\n\n")
                        out.write(f"{clean_content}\n\n")
                        out.write("---\n\n")
                        
                    elif step_type == "PLANNER_RESPONSE":
                        # Handle Assistant text response
                        if content:
                            out.write(f"### 🤖 Antigravity ({time_str})\n\n")
                            out.write(f"{content}\n\n")
                            out.write("---\n\n")
                        
                        # Show tool calls in a simplified way
                        tool_calls = step.get("tool_calls", [])
                        if tool_calls:
                            out.write("*⚙️ Wywołane narzędzia:*\n")
                            for tool in tool_calls:
                                name = tool.get("name", "")
                                args = tool.get("args", {})
                                out.write(f"- `{name}`")
                                if name == "run_command":
                                    cmd = args.get("CommandLine", "")
                                    out.write(f": uruchomienie komendy `{cmd[:100]}`")
                                out.write("\n")
                            out.write("\n---\n\n")
                            
                    elif step_type == "RUN_COMMAND" and step.get("status") == "DONE":
                        # If a command completed, show stdout/output briefly
                        out.write(f"*🖥️ Wynik komendy ({time_str}):*\n")
                        lines = content.splitlines()
                        # Show first 15 lines of output to avoid bloating
                        out.write("```\n")
                        for l in lines[:15]:
                            out.write(f"{l}\n")
                        if len(lines) > 15:
                            out.write("...\n")
                        out.write("```\n\n---\n\n")
                        
                except Exception as e:
                    # Ignore corrupted lines
                    continue

    print(f"Success: Formatted markdown written to {output_path}")

if __name__ == "__main__":
    convert()
