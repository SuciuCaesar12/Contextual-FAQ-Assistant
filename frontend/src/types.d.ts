type ChatMessage = {
    sender: "user" | "bot";
    text: string;
};

type ChatResponse = {
    source: string;
    matched_question: string;
    answer: string;
}