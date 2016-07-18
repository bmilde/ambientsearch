% BeamSearchKeywordExtraction

% Copyright (c) 2015 Idiap Research Institute, http://www.idiap.ch/
% Written by Maryam Habibi <Maryam.Habibi@idiap.ch> or <M1habiby@gmail.com>

% This file is part of the DocRec software.

% DocRec is free software: you can redistribute it and/or modify
% it under the terms of the GNU General Public License version 3 as
% published by the Free Software Foundation.

% DocRec is distributed in the hope that it will be useful,
% but WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
% GNU General Public License for more details.

% You should have received a copy of the GNU General Public License
% along with DocRec. If not, see <http://www.gnu.org/licenses/>.


function [outin outv] = BeamSearchKeywordExtraction(x, wP, xP,k, p , Sizewordsw,path)


options = optimset('GradObj','on', 'Display','off');
options.TolFun = 1e-10;
options.TolX = 1e-10;
options.MaxIter = 1000;

xind = find(x);
wtopics = wP(xind,:);

% Greedy : BeamSearch

B = 2; % size of the beam

w = zeros(B,size(xind,2));

gain = zeros(size(w));
pref = zeros(B,1);

thisRoundVal = 0;

thisRoundGain = w;
thisRound =w;
for kk=1:k,
    
    
    index = 1;
    if kk>1
        it = B;
    else
        it = 1;
    end

    for b=1:it,
       zeroElements = find(~w(b,:));
       wb = w(b,:);
       g= gain(b,:);
       pf = pref(b);
       
       if isempty(zeroElements),
           thisRound(index, :) = wb;
           [f ]=NoneLinearLatentSpaceEval( thisRound(index,:), wtopics, xP, p);
           thisRoundVal(index) = f;
           
           thisRoundGain(index,:) = g;
           index = index +1;
           continue;
       end
       for ii=1:length(zeroElements),
           el = zeroElements(ii);

           thisRound(index, :) = wb;
           thisRound(index, el)=1;
           
           [f ]=NoneLinearLatentSpaceEval( thisRound(index,:), wtopics, xP, p);
           thisRoundVal(index) = f;
           thisRoundGain(index,:) = g;
           thisRoundGain(index, el) = f-pf; 
           index = index +1;           
       end        
    end    
   for b =1:B,         
        [val ind] = max(thisRoundVal);        
        w(b,:) = thisRound(ind,:);       
        gain(b,:) = thisRoundGain(ind,:);
        thisRoundVal(ind)= min(thisRoundVal);
        pref(b) = val;          
   end   
    thisRoundVal = 0;
    thisRound = zeros(size(w));
    thisRoundGain = zeros(size(w));
end

maxval = 0;
maxw = 0;
maxgain=0;
for bb=1:B,
    val = NoneLinearLatentSpaceEval( w(bb,:), wtopics, xP, p);
    if val > maxval,
        maxval = val;
        maxw = w(bb,:);
        maxgain = gain(bb,:);
    end
end

fid=fopen([path '/W/1'],'w');
outv1=zeros(1,Sizewordsw);
outv=sparse(outv1);
outin=[];
for kk=1:k,
    
    [val ind] = max(maxgain);
    xind(ind);
    outin=[outin xind(ind)];
    %word = wordsw{xind(ind)};
    freq1=x(xind(ind));
    outv(xind(ind))=1;
    maxgain(ind)= min(maxgain);
   % outw{kk}= word;
    
     fprintf(fid , '%f\n', xind(ind));
end
fclose(fid);

end


function [f] = NoneLinearLatentSpaceEval(w , wtopics, xP, p)

    f =    sum(sum(repmat(w',1 , size(wtopics,2)).*wtopics .* repmat(xP, size(wtopics,1),1)).^p);

end

function [f df] = NoneLinearLatentSpace(w, wtopics, xP, p , lambda)
base = 0.001;
f1 =  sum(sum(repmat(w',1 , size(wtopics,2)).*wtopics .* repmat(xP, size(wtopics,1),1)+base).^p);
f2 = norm(lambda .*w, 1);
f1
f2
f = -f1 +  f2;
df1 = p*(sum(repmat(w',1 , size(wtopics,2)).*wtopics .* repmat(xP, size(wtopics,1),1)+ base).^(p-1));
df2 = sum(wtopics .* repmat(xP, size(wtopics,1),1));
df3 = sum(df1 .* df2);
df4 = (abs(w)./w);
df4(w==0) = 0;
df = - df3+ lambda .* df4;
end




