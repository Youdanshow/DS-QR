import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { useToast } from "../hooks/use-toast";
import { useAuth } from "../contexts/AuthContext";
import { QrCode, Download, History, Link, Trash2, Copy, AlertCircle } from "lucide-react";
import UserStatus from "./UserStatus";
import SubscriptionModal from "./SubscriptionModal";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const QRGenerator = () => {
  const [url, setUrl] = useState("");
  const [size, setSize] = useState("150x150");
  const [customSize, setCustomSize] = useState({ width: "", height: "" });
  const [generatedQR, setGeneratedQR] = useState(null);
  const [qrHistory, setQrHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const { toast } = useToast();
  const { limits, updateLimits, isLoading: authLoading } = useAuth();

  const sizePresets = [
    { label: "Small (150x150)", value: "150x150" },
    { label: "Medium (200x200)", value: "200x200" },
    { label: "Large (300x300)", value: "300x300" },
    { label: "Extra Large (400x400)", value: "400x400" },
    { label: "Custom", value: "custom" }
  ];

  useEffect(() => {
    // Load QR code history from API
    loadQRHistory();
  }, []);

  const loadQRHistory = async () => {
    try {
      const response = await axios.get(`${API}/qr/history`);
      setQrHistory(response.data.qrCodes);
      updateLimits(response.data.limits);
    } catch (error) {
      console.error('Failed to load QR history:', error);
    }
  };

  const validateURL = (inputUrl) => {
    try {
      const urlPattern = new RegExp(
        '^(https?:\\/\\/)?' + // protocol (optional)
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$','i' // fragment locator
      );
      return urlPattern.test(inputUrl) || new URL(inputUrl);
    } catch {
      return false;
    }
  };

  const generateQRCode = async () => {
    if (!url.trim()) {
      toast({
        title: "URL Required",
        description: "Please enter a URL to generate QR code",
        variant: "destructive"
      });
      return;
    }

    if (!validateURL(url)) {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid URL (e.g., https://example.com)",
        variant: "destructive"
      });
      return;
    }

    // Check if user has reached limit
    if (limits.max !== "unlimited" && limits.used >= limits.max) {
      setShowSubscriptionModal(true);
      return;
    }

    setIsLoading(true);

    try {
      // Determine the size to use
      let qrSize = size;
      if (size === "custom") {
        if (!customSize.width || !customSize.height) {
          toast({
            title: "Custom Size Required",
            description: "Please enter both width and height for custom size",
            variant: "destructive"
          });
          setIsLoading(false);
          return;
        }
        qrSize = `${customSize.width}x${customSize.height}`;
      }

      // Call backend API to generate QR code
      const response = await axios.post(`${API}/qr/generate`, {
        url: url,
        size: qrSize
      });

      const newQR = response.data.qrCode;
      setGeneratedQR(newQR);
      
      // Update limits and history
      updateLimits(response.data.limits);
      setQrHistory(prev => [newQR, ...prev]);

      toast({
        title: "QR Code Generated!",
        description: "Your QR code has been generated successfully",
      });

    } catch (error) {
      if (error.response?.status === 403) {
        // Limit reached
        setShowSubscriptionModal(true);
        toast({
          title: "Limite atteinte",
          description: error.response.data.detail,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Generation Failed",
          description: error.response?.data?.detail || "Failed to generate QR code. Please try again.",
          variant: "destructive"
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const downloadQRCode = async (qrItem) => {
    try {
      const response = await fetch(qrItem.qrCodeUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `qr-code-${qrItem.id}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Update download status in history
      setQrHistory(prev => 
        prev.map(item => 
          item.id === qrItem.id ? { ...item, downloaded: true } : item
        )
      );

      toast({
        title: "Downloaded!",
        description: "QR code image has been downloaded successfully",
      });
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to download QR code. Please try again.",
        variant: "destructive"
      });
    }
  };

  const deleteQRCode = async (qrId) => {
    try {
      await axios.delete(`${API}/qr/${qrId}`);
      setQrHistory(prev => prev.filter(item => item.id !== qrId));
      
      toast({
        title: "Deleted",
        description: "QR code has been deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: "Failed to delete QR code. Please try again.",
        variant: "destructive"
      });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "URL copied to clipboard",
    });
  };

  const clearHistory = async () => {
    setQrHistory([]);
    toast({
      title: "History Cleared",
      description: "QR code history has been cleared locally",
    });
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full">
              <QrCode className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              QR Code Generator
            </h1>
          </div>
          <p className="text-gray-600 text-lg">
            Generate and download QR codes for any URL with custom sizing options
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* User Status - New */}
          <div className="lg:col-span-1">
            <UserStatus />
          </div>

          {/* Generator Form */}
          <div className="lg:col-span-2">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Link className="h-5 w-5 text-blue-600" />
                  Create QR Code
                </CardTitle>
                {limits.max !== "unlimited" && limits.used >= limits.max && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <span className="text-red-700 text-sm">
                      Limite atteinte ({limits.used}/{limits.max}). 
                      <button 
                        onClick={() => setShowSubscriptionModal(true)}
                        className="underline ml-1 font-medium"
                      >
                        Passer au Premium
                      </button>
                    </span>
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-6">
                {/* URL Input */}
                <div className="space-y-2">
                  <Label htmlFor="url" className="text-sm font-medium">
                    Enter URL
                  </Label>
                  <Input
                    id="url"
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="h-12 text-base"
                  />
                </div>

                {/* Size Selection */}
                <div className="space-y-4">
                  <Label className="text-sm font-medium">QR Code Size</Label>
                  <Select value={size} onValueChange={setSize}>
                    <SelectTrigger className="h-12">
                      <SelectValue placeholder="Select size" />
                    </SelectTrigger>
                    <SelectContent>
                      {sizePresets.map((preset) => (
                        <SelectItem key={preset.value} value={preset.value}>
                          {preset.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Custom Size Inputs */}
                  {size === "custom" && (
                    <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div>
                        <Label htmlFor="width" className="text-sm">Width (px)</Label>
                        <Input
                          id="width"
                          type="number"
                          placeholder="300"
                          value={customSize.width}
                          onChange={(e) => setCustomSize(prev => ({ ...prev, width: e.target.value }))}
                          min="50"
                          max="1000"
                        />
                      </div>
                      <div>
                        <Label htmlFor="height" className="text-sm">Height (px)</Label>
                        <Input
                          id="height"
                          type="number"
                          placeholder="300"
                          value={customSize.height}
                          onChange={(e) => setCustomSize(prev => ({ ...prev, height: e.target.value }))}
                          min="50"
                          max="1000"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Generate Button */}
                <Button 
                  onClick={generateQRCode}
                  disabled={isLoading || (limits.max !== "unlimited" && limits.used >= limits.max)}
                  className="w-full h-12 text-base bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <QrCode className="h-5 w-5 mr-2" />
                      Generate QR Code
                    </>
                  )}
                </Button>

                {/* Generated QR Preview */}
                {generatedQR && (
                  <div className="p-6 bg-white rounded-lg border-2 border-dashed border-gray-200">
                    <div className="text-center space-y-4">
                      <h3 className="font-semibold text-lg">Generated QR Code</h3>
                      <img 
                        src={generatedQR.qrCodeUrl} 
                        alt="Generated QR Code"
                        className="mx-auto border rounded-lg shadow-sm"
                      />
                      <div className="flex flex-wrap gap-2 justify-center">
                        <Badge variant="secondary">{generatedQR.size}</Badge>
                        <Badge variant="outline">{new URL(generatedQR.url).hostname}</Badge>
                      </div>
                      <Button 
                        onClick={() => downloadQRCode(generatedQR)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download PNG
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* History Panel */}
          <div className="lg:col-span-1">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5 text-purple-600" />
                    History
                  </CardTitle>
                  {qrHistory.length > 0 && (
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={clearHistory}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {qrHistory.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">
                      No QR codes generated yet
                    </p>
                  ) : (
                    qrHistory.map((qrItem, index) => (
                      <div key={qrItem.id}>
                        <div className="space-y-3">
                          <div className="flex items-center justify-center">
                            <img 
                              src={qrItem.qrCodeUrl} 
                              alt="QR Code"
                              className="w-16 h-16 border rounded shadow-sm"
                            />
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600 truncate flex-1">
                                {new URL(qrItem.url).hostname}
                              </span>
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => copyToClipboard(qrItem.url)}
                                >
                                  <Copy className="h-3 w-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => deleteQRCode(qrItem.id)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <Badge variant="outline" className="text-xs">
                                {qrItem.size}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                {new Date(qrItem.createdAt).toLocaleDateString()}
                              </span>
                            </div>
                            
                            <Button 
                              size="sm" 
                              variant={qrItem.downloaded ? "secondary" : "default"}
                              onClick={() => downloadQRCode(qrItem)}
                              className="w-full"
                            >
                              <Download className="h-3 w-3 mr-1" />
                              {qrItem.downloaded ? "Downloaded" : "Download"}
                            </Button>
                          </div>
                        </div>
                        
                        {index < qrHistory.length - 1 && (
                          <Separator className="mt-4" />
                        )}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Subscription Modal */}
        <SubscriptionModal 
          isOpen={showSubscriptionModal} 
          onClose={() => setShowSubscriptionModal(false)} 
        />
      </div>
    </div>
  );
};

export default QRGenerator;