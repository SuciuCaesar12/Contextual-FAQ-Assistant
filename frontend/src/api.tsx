import axios from 'axios';

const askQuestion = (question: string): Promise<ChatResponse> => {
  console.log("Sending question to backend...");
  return axios.post('http://127.0.0.1:8000/ask-question', {
    user_question: question,
  }, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then((response) => response.data);
};

export default askQuestion;