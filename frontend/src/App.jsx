import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ShoppingBag, Loader2, Package, Truck, CreditCard, Phone, AlertCircle } from 'lucide-react';
import './index.css'   // 🔥 indispensable pour activer Tailwind

const API_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "Marhba bik ! 👋\n\nBienvenue dans notre boutique de vêtements en Tunisie. Je suis là pour vous aider avec :\n\n• Nos collections et produits\n• Les tailles et disponibilités\n• La livraison en Tunisie\n• Les paiements et retours\n\nComment puis-je vous aider ?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking'); // checking, online, offline
  const messagesEndRef = useRef(null);

  // Vérifier le statut de l'API au démarrage
  useEffect(() => {
    checkAPIStatus();
  }, []);

  const checkAPIStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/`);
      const data = await response.json();
      
      if (data.status) {
        setApiStatus('online');
        console.log('✅ Backend connecté:', data);
      } else {
        setApiStatus('offline');
      }
    } catch (error) {
      console.error('❌ Backend non accessible:', error);
      setApiStatus('offline');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      text: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsTyping(true);

    try {
      // Appel à l'API Backend
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput
        })
      });

      if (!response.ok) {
        throw new Error('Erreur API');
      }

      const data = await response.json();
      
      const botResponse = {
        id: messages.length + 2,
        type: 'bot',
        text: data.response || "Désolé, je n'ai pas pu traiter votre demande.",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botResponse]);
      
    } catch (error) {
      console.error('Erreur:', error);
      
      const errorMessage = {
        id: messages.length + 2,
        type: 'bot',
        text: "Désolé, une erreur s'est produite. Veuillez vérifier que le serveur backend est bien démarré sur http://localhost:8000",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      setApiStatus('offline');
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickQuestions = [
    "Quels vêtements vendez-vous ?",
    "Avez-vous des t-shirts ?",
    "Quel est le prix du jean ?",
    "Comment fonctionne la livraison ?"
  ];

  const handleQuickQuestion = (question) => {
    setInputValue(question);
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header Noir et Blanc */}
      <div className="bg-black text-white shadow-2xl p-6 border-b-4 border-white">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white p-3 rounded-lg">
                <ShoppingBag className="text-black" size={32} />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-wider">BOUTIQUE TN</h1>
                <p className="text-sm text-gray-300 mt-1">Mode & Élégance • Livraison en Tunisie</p>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Truck size={18} />
                <span>Livraison rapide</span>
              </div>
              <div className="flex items-center gap-2">
                <CreditCard size={18} />
                <span>Paiement sécurisé</span>
              </div>
              {/* Indicateur de statut API */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  apiStatus === 'online' ? 'bg-green-500' : 
                  apiStatus === 'offline' ? 'bg-red-500' : 
                  'bg-yellow-500 animate-pulse'
                }`}></div>
                <span className="text-xs">
                  {apiStatus === 'online' ? 'IA Active' : 
                   apiStatus === 'offline' ? 'Hors ligne' : 
                   'Connexion...'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alerte si backend offline */}
      {apiStatus === 'offline' && (
        <div className="bg-red-100 border-l-4 border-red-500 p-4">
          <div className="max-w-6xl mx-auto flex items-center gap-3">
            <AlertCircle className="text-red-500" size={24} />
            <div>
              <p className="text-red-700 font-semibold">Backend non connecté</p>
              <p className="text-red-600 text-sm">
                Assurez-vous que le serveur est démarré avec: <code className="bg-red-200 px-2 py-1 rounded">python main.py</code>
              </p>
            </div>
            <button 
              onClick={checkAPIStatus}
              className="ml-auto bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 text-sm"
            >
              Réessayer
            </button>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-4 ${
                message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`p-3 rounded-xl flex-shrink-0 ${
                  message.type === 'user'
                    ? 'bg-black shadow-lg'
                    : 'bg-white border-2 border-black'
                }`}
              >
                {message.type === 'user' ? (
                  <User className="text-white" size={24} />
                ) : (
                  <Bot className="text-black" size={24} />
                )}
              </div>
              <div
                className={`max-w-[75%] p-5 rounded-2xl shadow-lg ${
                  message.type === 'user'
                    ? 'bg-black text-white rounded-tr-none'
                    : 'bg-white text-black border-2 border-gray-200 rounded-tl-none'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-line font-medium">{message.text}</p>
                <span className={`text-xs mt-3 block ${
                  message.type === 'user' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  {message.timestamp.toLocaleTimeString('fr-TN', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-white border-2 border-black">
                <Bot className="text-black" size={24} />
              </div>
              <div className="bg-white border-2 border-gray-200 p-5 rounded-2xl rounded-tl-none shadow-lg">
                <div className="flex gap-2 items-center">
                  <Loader2 className="animate-spin text-black" size={20} />
                  <span className="text-sm text-gray-600">L'IA réfléchit...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Questions */}
      {messages.length <= 1 && (
        <div className="px-6 pb-6 bg-gray-50">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white border-2 border-black rounded-xl p-6 shadow-lg">
              <p className="text-sm text-black mb-4 font-bold flex items-center gap-2">
                <Package size={18} />
                Questions fréquentes :
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {quickQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleQuickQuestion(question)}
                    className="text-left text-sm bg-white hover:bg-black hover:text-white p-4 rounded-lg border-2 border-black transition-all duration-300 font-medium shadow-sm hover:shadow-md"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-black p-6 shadow-2xl border-t-4 border-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Écrivez votre message..."
              disabled={apiStatus === 'offline'}
              className="flex-1 p-4 bg-white border-2 border-white rounded-xl focus:outline-none focus:ring-4 focus:ring-gray-400 text-black font-medium text-base disabled:bg-gray-300 disabled:cursor-not-allowed"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || apiStatus === 'offline'}
              className="bg-white text-black px-8 py-4 rounded-xl hover:bg-gray-200 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed transition-all duration-300 font-bold shadow-lg hover:shadow-xl"
            >
              <Send size={24} />
            </button>
          </div>
          <div className="flex items-center justify-between mt-4 text-xs text-gray-400">
            <span className="flex items-center gap-2">
              <Phone size={14} />
              {apiStatus === 'online' ? 'IA Groq connectée' : 'Mode hors ligne'}
            </span>
            <span>Appuyez sur Entrée pour envoyer</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;