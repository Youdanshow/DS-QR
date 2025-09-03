import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { Crown, Check, Zap, Infinity } from 'lucide-react';

const SubscriptionModal = ({ isOpen, onClose }) => {
  const [isLoading, setIsLoading] = useState(false);
  const { upgradeToPremium, limits } = useAuth();
  const { toast } = useToast();

  const handleUpgrade = async () => {
    setIsLoading(true);
    
    const result = await upgradeToPremium();
    
    if (result.success) {
      toast({
        title: "Félicitations! 🎉",
        description: "Vous êtes maintenant Premium avec génération illimitée de QR codes!",
      });
      onClose();
    } else {
      toast({
        title: "Erreur d'abonnement",
        description: result.error,
        variant: "destructive"
      });
    }
    
    setIsLoading(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl flex items-center justify-center gap-2">
            <Crown className="h-6 w-6 text-yellow-500" />
            Passer au Premium
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Current Status */}
          <div className="text-center p-4 bg-red-50 rounded-lg border border-red-200">
            <p className="text-red-700 font-medium">
              Limite atteinte: {limits.used}/{limits.max === "unlimited" ? "∞" : limits.max} QR codes utilisés
            </p>
          </div>

          {/* Premium Features */}
          <Card className="border-2 border-gradient-to-r from-yellow-400 to-yellow-600">
            <CardHeader className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Crown className="h-8 w-8 text-yellow-500" />
                <CardTitle className="text-2xl">Premium Monthly</CardTitle>
              </div>
              <div className="text-3xl font-bold text-yellow-600">
                €9.99<span className="text-lg font-normal text-gray-500">/mois</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-1">
                    <Check className="h-4 w-4 text-green-600" />
                  </div>
                  <span className="flex items-center gap-2">
                    <Infinity className="h-4 w-4 text-blue-600" />
                    Génération illimitée de QR codes
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-1">
                    <Check className="h-4 w-4 text-green-600" />
                  </div>
                  <span className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-purple-600" />
                    Tailles personnalisées avancées
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-1">
                    <Check className="h-4 w-4 text-green-600" />
                  </div>
                  <span>Historique complet sans limite</span>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-green-100 p-1">
                    <Check className="h-4 w-4 text-green-600" />
                  </div>
                  <span>Support prioritaire</span>
                </div>
              </div>
              
              <Button 
                onClick={handleUpgrade}
                disabled={isLoading}
                className="w-full h-12 text-base bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white"
                size="lg"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2" />
                    Activation en cours...
                  </>
                ) : (
                  <>
                    <Crown className="h-5 w-5 mr-2" />
                    Passer au Premium
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Plan Comparison */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="text-center">
              <Badge variant="outline">Invité</Badge>
              <p className="mt-1 text-gray-600">3 QR codes</p>
            </div>
            <div className="text-center">
              <Badge variant="secondary">Standard</Badge>
              <p className="mt-1 text-gray-600">5 QR codes</p>
            </div>
            <div className="text-center">
              <Badge className="bg-gradient-to-r from-yellow-500 to-yellow-600">Premium</Badge>
              <p className="mt-1 text-gray-600">Illimité</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SubscriptionModal;