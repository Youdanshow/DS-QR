import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { Crown, Gift, Sparkles, Code, Star } from 'lucide-react';

const FounderModal = ({ isOpen, onClose }) => {
  const [promoCode, setPromoCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { redeemPromoCode } = useAuth();
  const { toast } = useToast();

  const handleRedeemCode = async (e) => {
    e.preventDefault();
    
    if (!promoCode.trim()) {
      toast({
        title: "Code requis",
        description: "Veuillez saisir un code promo",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    
    const result = await redeemPromoCode(promoCode);
    
    if (result.success) {
      toast({
        title: "🎉 Félicitations Founder !",
        description: "Vous avez maintenant un accès permanent illimité !",
      });
      setPromoCode('');
      onClose();
    } else {
      toast({
        title: "Code invalide",
        description: result.error,
        variant: "destructive"
      });
    }
    
    setIsLoading(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-xl flex items-center justify-center gap-2">
            <Gift className="h-6 w-6 text-purple-600" />
            Code Promo Founder
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Founder Benefits */}
          <Card className="border-2 border-gradient-to-r from-purple-400 to-pink-400">
            <CardContent className="p-4">
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <Crown className="h-8 w-8 text-yellow-500" />
                  <h3 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    Accès Founder
                  </h3>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <Sparkles className="h-4 w-4 text-purple-500" />
                    <span>Génération QR <strong>illimitée à vie</strong></span>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span>Badge <strong>Founder</strong> exclusif</span>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <Crown className="h-4 w-4 text-purple-500" />
                    <span>Accès <strong>permanent</strong> sans expiration</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Promo Code Form */}
          <form onSubmit={handleRedeemCode} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="promo-code" className="text-sm font-medium">
                Code Promo
              </Label>
              <div className="relative">
                <Code className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="promo-code"
                  type="text"
                  placeholder="Entrez votre code promo"
                  value={promoCode}
                  onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                  className="pl-10 font-mono"
                  required
                />
              </div>
            </div>
            
            <Button 
              type="submit" 
              className="w-full h-12 text-base bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                  Activation...
                </>
              ) : (
                <>
                  <Gift className="h-4 w-4 mr-2" />
                  Utiliser le Code
                </>
              )}
            </Button>
          </form>
          
          {/* Info */}
          <div className="text-center text-xs text-gray-500 p-3 bg-gray-50 rounded-lg">
            <p>Les codes promo Founder donnent un accès premium permanent sans abonnement mensuel.</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default FounderModal;