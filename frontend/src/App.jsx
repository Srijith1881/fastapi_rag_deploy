import { useState } from "react";
import { Upload, MessageSquare, FileText, Send, Loader2 } from "lucide-react";

function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [query, setQuery] = useState("");
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const API_BASE = "http://127.0.0.1:8000"; // Change if backend hosted elsewhere

  const handleUpload = async () => {
    if (!pdfFile) {
      alert("Please select a PDF file first");
      return;
    }
    const formData = new FormData();
    formData.append("file", pdfFile);

    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      alert(data.message);
    } catch (err) {
      console.error(err);
      alert("Error uploading file");
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      alert("Please enter a question");
      return;
    }
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setChat((prev) => [...prev, { question: query, answer: data.reply }]);
      setQuery("");
    } catch (err) {
      console.error(err);
      alert("Error fetching answer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4">
            <FileText className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-2">
            RAG PDF Chat
          </h1>
          <p className="text-slate-400 text-lg">Upload PDFs and chat with your documents using AI</p>
        </div>

        {/* Upload Section */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
          <div className="flex items-center mb-6">
            <Upload className="w-6 h-6 text-blue-400 mr-3" />
            <h2 className="text-xl font-semibold text-white">Upload Document</h2>
          </div>
          
          <div className="space-y-4">
            <div className="relative">
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setPdfFile(e.target.files[0])}
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-xl text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-500 file:text-white hover:file:bg-blue-600 file:cursor-pointer transition-colors"
              />
            </div>
            
            {pdfFile && (
              <div className="flex items-center text-sm text-slate-300 bg-slate-700/30 rounded-lg p-3">
                <FileText className="w-4 h-4 mr-2 text-blue-400" />
                Selected: {pdfFile.name}
              </div>
            )}
            
            <button
              onClick={handleUpload}
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-slate-600 disabled:to-slate-600 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload PDF</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Query Section */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 mb-8 shadow-2xl">
          <div className="flex items-center mb-6">
            <MessageSquare className="w-6 h-6 text-green-400 mr-3" />
            <h2 className="text-xl font-semibold text-white">Ask Questions</h2>
          </div>
          
          <div className="space-y-4">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about the uploaded PDFs..."
              className="w-full p-4 bg-slate-700/50 border border-slate-600 rounded-xl text-white placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              rows={4}
            />
            <button
              onClick={handleQuery}
              disabled={loading}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-slate-600 disabled:to-slate-600 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Thinking...</span>
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span>Ask Question</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Chat Section */}
        {chat.length > 0 && (
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
            <div className="flex items-center mb-6">
              <MessageSquare className="w-6 h-6 text-purple-400 mr-3" />
              <h2 className="text-xl font-semibold text-white">Conversation History</h2>
            </div>
            
            <div className="space-y-6 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-track-slate-700 scrollbar-thumb-slate-500">
              {chat.map((c, idx) => (
                <div key={idx} className="bg-slate-700/30 border border-slate-600/30 rounded-xl p-6 hover:bg-slate-700/40 transition-colors">
                  <div className="mb-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-sm font-medium">Q</span>
                      </div>
                      <div className="flex-1">
                        <p className="text-blue-300 font-medium leading-relaxed">{c.question}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm font-medium">A</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-green-200 leading-relaxed">{c.answer}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {chat.length === 0 && (
          <div className="text-center py-12">
            <div className="w-24 h-24 bg-slate-700/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-12 h-12 text-slate-500" />
            </div>
            <p className="text-slate-400 text-lg">No conversations yet. Upload a PDF and start asking questions!</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;