import React, { useState } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { useAuth } from '../contexts/AuthContext';
import AuthModal from './AuthModal';
import SubscriptionModal from './SubscriptionModal';
import FounderModal from './FounderModal';
import { LogOut, Crown, Users, Chrome, Gift, Star } from 'lucide-react';

const UserStatus = () => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showSubscriptionModal, setShowSubscriptionModal] = useState(false);
  const [showFounderModal, setShowFounderModal] = useState(false);
  const { user, limits, isAuthenticated, logout } = useAuth();

  const getLimitColor = () => {
    if (limits.max === "unlimited") return "bg-gradient-to-r from-yellow-500 to-yellow-600";
    
    const percentage = (limits.used / limits.max) * 100;
    if (percentage >= 100) return "bg-red-500";
    if (percentage >= 80) return "bg-orange-500";
    return "bg-green-500";
  };

  const getLimitBadgeVariant = () => {
    if (limits.isFounder) return "default";
    if (limits.isPremium) return "default";
    if (limits.used >= limits.max) return "destructive";
    return "secondary";
  };

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getUserBadge = () => {
    if (limits.isFounder) {
      return (
        <Badge className="text-xs bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          <Star className="h-3 w-3 mr-1" />
          Founder
        </Badge>
      );
    } else if (limits.isPremium) {
      return (
        <Badge className="text-xs bg-gradient-to-r from-yellow-500 to-yellow-600 text-white">
          <Crown className="h-3 w-3 mr-1" />
          Premium
        </Badge>
      );
    }
    return null;
  };

  return (
    <>
      <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-md">
        <CardContent className="p-4">
          {isAuthenticated ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src={user.picture} alt={user.name} />
                    <AvatarFallback className="bg-blue-500 text-white text-sm">
                      {getInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm truncate">{user.name}</p>
                      {getUserBadge()}
                    </div>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={logout}
                  className="h-8 px-2 text-gray-600 hover:text-gray-800"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">QR codes utilisés</span>
                  <Badge variant={getLimitBadgeVariant()} className="text-xs">
                    {limits.used}/{limits.max === "unlimited" ? "∞" : limits.max}
                  </Badge>
                </div>
                
                {limits.max !== "unlimited" && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${getLimitColor()}`}
                      style={{ width: `${Math.min((limits.used / limits.max) * 100, 100)}%` }}
                    ></div>
                  </div>
                )}
                
                {/* Action Buttons */}
                <div className="flex gap-2">
                  {!limits.isFounder && !limits.isPremium && limits.used >= limits.max && (
                    <Button 
                      size="sm" 
                      onClick={() => setShowSubscriptionModal(true)}
                      className="flex-1 h-8 text-xs bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700"
                    >
                      <Crown className="h-3 w-3 mr-1" />
                      Premium
                    </Button>
                  )}
                  
                  {!limits.isFounder && (
                    <Button 
                      size="sm" 
                      onClick={() => setShowFounderModal(true)}
                      variant="outline"
                      className="flex-1 h-8 text-xs border-purple-200 text-purple-600 hover:bg-purple-50"
                    >
                      <Gift className="h-3 w-3 mr-1" />
                      Code Promo
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-gray-500" />
                <span className="font-medium text-sm text-gray-700">Mode Invité</span>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">QR codes utilisés</span>
                  <Badge variant={limits.used >= limits.max ? "destructive" : "secondary"} className="text-xs">
                    {limits.used}/{limits.max}
                  </Badge>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getLimitColor()}`}
                    style={{ width: `${Math.min((limits.used / limits.max) * 100, 100)}%` }}
                  ></div>
                </div>
                
                <Button 
                  size="sm" 
                  onClick={() => setShowAuthModal(true)}
                  className="w-full h-8 text-xs bg-white hover:bg-gray-50 text-gray-900 border border-gray-300"
                >
                  <Chrome className="h-3 w-3 mr-1 text-red-500" />
                  Se connecter (+2 QR codes)
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />
      
      <SubscriptionModal 
        isOpen={showSubscriptionModal} 
        onClose={() => setShowSubscriptionModal(false)} 
      />
      
      <FounderModal 
        isOpen={showFounderModal} 
        onClose={() => setShowFounderModal(false)} 
      />
    </>
  );
};

export default UserStatus;