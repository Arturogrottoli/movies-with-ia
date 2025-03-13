document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chat-messages")
    const chatForm = document.getElementById("chat-form")
    const userInput = document.getElementById("user-input")
  
    // Chat history to keep track of the conversation
    let chatHistory = []
  
    // Function to add a message to the chat
    function addMessage(content, sender) {
      const messageDiv = document.createElement("div")
      messageDiv.classList.add("chat-message", sender === "user" ? "text-right" : "text-left")
  
      const messageBubble = document.createElement("div")
      messageBubble.classList.add(
        "inline-block",
        "max-w-[80%]",
        "p-3",
        "rounded-lg",
        sender === "user" ? "bg-purple-600" : "bg-gray-200",
        sender === "user" ? "text-white" : "text-gray-800",
      )
  
      // Process markdown-like syntax for bot messages
      if (sender === "bot") {
        // Convert **text** to bold
        content = content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
  
        // Convert [text](url) to links
        content = content.replace(
          /\[(.*?)\]$$(.*?)$$/g,
          '<a href="$2" target="_blank" class="text-blue-600 underline">$1</a>',
        )
  
        // Convert line breaks to <br>
        content = content.replace(/\n/g, "<br>")
      }
  
      messageBubble.innerHTML = content
      messageDiv.appendChild(messageBubble)
  
      chatMessages.appendChild(messageDiv)
  
      // Animate the message appearance
      setTimeout(() => {
        messageDiv.classList.add("show")
      }, 100)
  
      // Scroll to the bottom
      chatMessages.scrollTop = chatMessages.scrollHeight
    }
  
    // Function to show typing indicator
    function showTypingIndicator() {
      const typingDiv = document.createElement("div")
      typingDiv.id = "typing-indicator"
      typingDiv.classList.add("chat-message", "text-left")
  
      const typingBubble = document.createElement("div")
      typingBubble.classList.add("inline-block", "p-3", "rounded-lg", "bg-gray-200", "typing-indicator")
  
      typingBubble.innerHTML = "<span>.</span><span>.</span><span>.</span>"
      typingDiv.appendChild(typingBubble)
  
      chatMessages.appendChild(typingDiv)
      typingDiv.classList.add("show")
  
      // Scroll to the bottom
      chatMessages.scrollTop = chatMessages.scrollHeight
    }
  
    // Function to remove typing indicator
    function removeTypingIndicator() {
      const typingIndicator = document.getElementById("typing-indicator")
      if (typingIndicator) {
        typingIndicator.remove()
      }
    }
  
    // Function to send message to the server
    async function sendMessage(message) {
      showTypingIndicator()
  
      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: message,
            history: chatHistory,
          }),
        })
  
        const data = await response.json()
  
        // Update chat history
        chatHistory = data.history
  
        // Remove typing indicator and add bot response
        removeTypingIndicator()
        addMessage(data.response, "bot")
      } catch (error) {
        console.error("Error:", error)
        removeTypingIndicator()
        addMessage("Lo siento, ha ocurrido un error al procesar tu mensaje.", "bot")
      }
    }
  
    // Handle form submission
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault()
  
      const message = userInput.value.trim()
      if (message) {
        // Add user message to chat
        addMessage(message, "user")
  
        // Clear input
        userInput.value = ""
  
        // Send message to server
        sendMessage(message)
      }
    })
  
    // Send welcome message when the page loads
    setTimeout(() => {
      addMessage(
        "¡Hola! ¿Qué tipo de película te gustaría ver hoy? (Acción, Comedia, Terror, Ciencia Ficción, Drama, etc.)",
        "bot",
      )
    }, 500)
  })
  
  