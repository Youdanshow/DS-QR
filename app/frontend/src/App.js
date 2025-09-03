import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import QRGenerator from "./components/QRGenerator";
import { Toaster } from "./components/ui/toaster";
import { AuthProvider } from "./contexts/AuthContext";

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<QRGenerator />} />
            <Route path="/profile" element={<QRGenerator />} />
          </Routes>
        </BrowserRouter>
        <Toaster />
      </div>
    </AuthProvider>
  );
}

export default App;