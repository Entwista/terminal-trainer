generate_jq_question() {
  local number=$1
  curl -s -X POST https://api.openai.com/v1/chat/completions   -H "Authorization: Bearer $OPENAI_API_KEY"   -H "Content-Type: application/json"   -d "$(jq -n \
      --arg prompt "$(cat jq_user_prompt.txt)" \
      '{
        model: "gpt-4.1-mini",
        messages: [
          { role: "system", content: "You are ChatGPT, a helpful assistant." },
          { role: "user", content: $prompt }
        ],
        temperature: 1
      }')"   | jq -r '.choices[0].message.content'   | sed -n '/^```bash/,/^```/p'   | sed '1d;$d' > "q_jq_${number}.sh"
}
for i in {1..10}; do generate_jq_question $i; done

generate_find_question() {
  local number=$1
  curl -s -X POST https://api.openai.com/v1/chat/completions   -H "Authorization: Bearer $OPENAI_API_KEY"   -H "Content-Type: application/json"   -d "$(jq -n \
      --arg prompt "$(cat find_user_prompt.txt)" \
      '{
        model: "gpt-4.1-mini",
        messages: [
          { role: "system", content: "You are ChatGPT, a helpful assistant." },
          { role: "user", content: $prompt }
        ],
        temperature: 1
      }')"   | jq -r '.choices[0].message.content'   | sed -n '/^```bash/,/^```/p'   | sed '1d;$d' > "q_find_${number}.sh"
}
for i in {1..10}; do generate_find_question $i; done