// Toggle chatbot visibility
function toggleChat() {
    const chatbox = document.getElementById("chatbot");
    chatbox.style.display = chatbox.style.display === "flex" ? "none" : "flex";
}

// Disable input and send button initially
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("user-input").disabled = true;
    document.getElementById("send-btn").disabled = true;
});

// Open chatbot when FOODCHOW AI button is clicked
document.querySelector(".ray-btn").addEventListener("click", function () {
    toggleChat();
});

// Function to send message
function sendMessage() {
    const inputField = document.getElementById("user-input");
    const message = inputField.value.trim();
    if (message === "") return;

    const chatBody = document.getElementById("chat-body");
    const selectedLanguage = document.getElementById("language-select").value; // Get selected language

    // Append user message to chat
    const userMessageContainer = document.createElement("div");
    userMessageContainer.className = "message-container user-message-container";

    const userIcon = document.createElement("img");
    userIcon.src = "static/man.png";
    userIcon.alt = "User Icon";
    userIcon.className = "message-icon";

    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.innerText = message;    

    userMessageContainer.appendChild(userMessage);
    userMessageContainer.appendChild(userIcon);
    chatBody.appendChild(userMessageContainer);

    // Show "typing..." indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "bot-message typing-indicator";
    typingIndicator.innerText = "typing...";
    chatBody.appendChild(typingIndicator);

    // Scroll to latest message
    chatBody.scrollTop = chatBody.scrollHeight;

    // Send message to backend
    fetch("http://192.168.1.26:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, language: selectedLanguage }),
    })
        .then(response => response.json())
        .then(data => {
            let botReply = data.response;

            // Ensure botReply is a string
            if (typeof botReply !== "string") {
                botReply = JSON.stringify(botReply, null, 2);
            }

            // Remove typing indicator
            chatBody.removeChild(typingIndicator);

            // Type bot's response letter by letter
            typeMessage(botReply, chatBody);
        })
        .catch(error => {
            console.error("Error:", error);

            // Remove typing indicator
            chatBody.removeChild(typingIndicator);

            // Show error message in chat
            typeMessage("Sorry for the inconvenience. We are currently experiencing a technical problem. Please try again in a little while....", chatBody);
        });

    inputField.value = ""; // Clear input field
}

// Allow "Enter" key to send message
document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// // Function to display message with **letter-by-letter** effect
// function typeMessage(text, chatBody) {
//     // Create bot message container
//     const botMessageContainer = document.createElement("div");
//     botMessageContainer.className = "message-container bot-message-container";

//     // Add bot icon
//     const botIcon = document.createElement("img");
//     botIcon.src = "static/F.png"; // Replace with your bot icon path
//     botIcon.alt = "Bot Icon";
//     botIcon.className = "message-icon";

//     // Add bot message
//     const botMessage = document.createElement("div");
//     botMessage.className = "bot-message";

//     // Append icon and message to container
//     botMessageContainer.appendChild(botIcon);
//     botMessageContainer.appendChild(botMessage);

//     // Append container to chat body
//     chatBody.appendChild(botMessageContainer);

//     // Type the message letter by letter
//     let i = 0;
//     function typingEffect() {
//         if (i < text.length) {
//             botMessage.innerHTML += text[i]; // Append letter by letter
//             i++;
//             setTimeout(typingEffect, 25); // Adjust speed (lower = faster)
//         }

//         // Scroll to latest message
//         chatBody.scrollTop = chatBody.scrollHeight;
//     }

//     typingEffect();
// }

// Function to display message with letter-by-letter effect
function typeMessage(text, chatBody) {
    // Create bot message container
    const botMessageContainer = document.createElement("div");
    botMessageContainer.className = "message-container bot-message-container";

    // Add bot icon
    const botIcon = document.createElement("img");
    botIcon.src = "static/robot1.png"; // Replace with your bot icon path
    botIcon.alt = "Bot Icon";
    botIcon.className = "message-icon";

    // Add bot message container
    const botMessage = document.createElement("div");
    botMessage.className = "bot-message";

    // Append icon and message to container
    botMessageContainer.appendChild(botIcon);
    botMessageContainer.appendChild(botMessage);

    // Append container to chat body
    chatBody.appendChild(botMessageContainer);

    // Format text: Convert step titles to bold
    let formattedText = text.replace(/\*\s*(.+?):/g, "<strong>$1:</strong>");

    // ✅ Convert email and URLs to clickable links
    formattedText = formattedText
        .replace(/href="mailto:([^"]+)"\>([^<]+)/g, '<a href="mailto:$1">$2</a>')
        .replace(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g, '<a href="mailto:$1">$1</a>')
        .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');

    // Split text into words for smooth typing
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = formattedText;
    const wordArray = tempDiv.textContent.split(" ");
    let i = 0;

    function typingEffect() {
        if (i < wordArray.length) {
            const currentWord = wordArray[i];
            const safeHTML = formattedText.match(new RegExp(`(<a[^>]+>${currentWord}</a>|${currentWord})`, 'i'));
            if (safeHTML) {
                botMessage.innerHTML += safeHTML[0] + " ";
            } else {
                botMessage.innerHTML += currentWord + " ";
            }
            i++;
            setTimeout(typingEffect, 50); // Adjust speed
        }

        // Scroll to latest message
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    typingEffect();
}

// // Function to display message with letter-by-letter effect
// function typeMessage(text, chatBody) {
//     // Create bot message container
//     const botMessageContainer = document.createElement("div");
//     botMessageContainer.className = "message-container bot-message-container";

//     // Add bot icon
//     const botIcon = document.createElement("img");
//     botIcon.src = "static/robot1.png"; // Replace with your bot icon path
//     botIcon.alt = "Bot Icon";
//     botIcon.className = "message-icon";

//     // Add bot message container
//     const botMessage = document.createElement("div");
//     botMessage.className = "bot-message";

//     // Append icon and message to container
//     botMessageContainer.appendChild(botIcon);
//     botMessageContainer.appendChild(botMessage);

//     // Append container to chat body
//     chatBody.appendChild(botMessageContainer);

//     // Format text: Convert step titles to bold
//     let formattedText = text.replace(/\*\s*(.+?):/g, "<strong>$1:</strong>");  // Bold titles

//     // Split text into words for smooth typing
//     let words = formattedText.split(" ");
//     let i = 0;

//     function typingEffect() {
//         if (i < words.length) {
//             botMessage.innerHTML += words[i] + " ";  // Append word by word
//             i++;
//             setTimeout(typingEffect, 50); // Adjust speed (lower = faster)
//         }

//         // Scroll to latest message
//         chatBody.scrollTop = chatBody.scrollHeight;
//     }

//     typingEffect();
// }

// Allow "Enter" key to send message
document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

function handleOption(option) {
    let message = "";
    if (option === "grow-online") {
        message = "I want to grow my restaurant online";
    } else if (option === "partner") {
        message = "I want to partner with FoodChow";
    } else if (option === "know-more") {
        message = "I want to know other Information";
    }

    // Remove the option buttons from UI
    const optionsDiv = document.querySelector(".bot-options");
    if (optionsDiv) {
        optionsDiv.remove();
    }
    // Set the message in the input field and trigger sendMessage()
    const inputField = document.getElementById("user-input");
    inputField.value = message;
    
    // Auto-send the selected option
    sendMessage();
    inputField.disabled = false;
    document.getElementById("send-btn").disabled = false;


    // Enable the input and button
    
}
