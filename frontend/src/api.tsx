const BACKEND_URL = "/api"  

const askQuestion = (question: string): Promise<ChatResponse> => {
    console.log("Sending question to backend...")
    return fetch(`${BACKEND_URL}/ask-question`, {
        method: "POST",
        body: JSON.stringify({'user_question': question}),
        headers: {
            "Content-Type": "application/json",
        },
    }).then((response) => response.json());
}

export default askQuestion;