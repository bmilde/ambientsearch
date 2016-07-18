function dlmcell(file,cell_array,varargin)
%% <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><> %%
% <><><><><>     dlmcell - Write Cell Array to Text File      <><><><><> %
% <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><> %
%                                                 Version:    01.06.2010 %
%                                                     (c) Roland Pfister %
%                                             roland_pfister@t-online.de %
% 1. Synopsis                                                            %
%                                                                        %
% A single cell array is written to an output file. Cells may consist of %
% any combination of (a) numbers, (b) letters, or (c) words. The inputs  %
% are as follows:                                                        %
%                                                                        %
%       - file       The output filename (string).                       %
%       - cell_array The cell array to be written.                       %
%       - delimiter  Delimiter symbol, e.g. ',' (optional;               %
%                    default: tab ('\t'}).                               %
%       - append     '-a' for appending the content to the               %
%                    output file (optional).                             %
%                                                                        %
% 2. Example                                                             %
%                                                                        %
%         mycell = {'Numbers', 'Letters', 'Words','More Words'; ...      %
%                    1, 'A', 'Apple', {'Apricot'}; ...                   %
%                    2, 'B', 'Banana', {'Blueberry'}; ...                %
%                    3, 'C', 'Cherry', {'Cranberry'}; };                 %
%         dlmcell('mytext.txt',mycell);                                  %
%                                                                        %
% <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><> %

% Copyright (c) 2014, Roland Pfister
% All rights reserved.

% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are
% met:

%    * Redistributions of source code must retain the above copyright
%      notice, this list of conditions and the following disclaimer.
%    * Redistributions in binary form must reproduce the above copyright
%      notice, this list of conditions and the following disclaimer in
%      the documentation and/or other materials provided with the distribution

% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
% AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
% IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
% ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
% LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
% CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
% SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
% INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
% CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
% ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
% POSSIBILITY OF SUCH DAMAGE.



%% Check input arguments
if nargin < 2
    disp('Error - Give at least two input arguments!'); 
    return;
elseif nargin > 4
    disp('Error - Do not give more than 4 input arguments!'); 
    return;
end
if ~ischar(file)
    disp(['Error - File input has to be a string (e.g. ' ...
        char(39) 'output.txt' char(39) '!']); 
    return;
end;
if ~iscell(cell_array)
    disp('Error - Input cell_array not of the type "cell"!'); 
    return;
end;
delimiter = '\t';
append = 'w';
if nargin > 2
    for i = 1:size(varargin,2)
        if strcmp('-a',varargin{1,i}) == 1
            append = 'a';
        else
            delimiter = varargin{1,i};
        end;
    end;
end

%% Open output file and prepare output array.
output_file = fopen(file,append);
output = cell(size(cell_array,1),size(cell_array,2));

%% Evaluate and write input array.
for i = 1:size(cell_array,1)
for j = 1:size(cell_array,2)
    if numel(cell_array{i,j}) == 0
        output{i,j} = '';
    % Check whether the content of cell i,j is
    % numeric and convert numbers to strings.
    elseif isnumeric(cell_array{i,j}) || islogical(cell_array{i,j})
        output{i,j} = num2str(cell_array{i,j}(1,1));
    
    % Check whether the content of cell i,j is another cell (e.g. a
    % string of length > 1 that was stored as cell. If cell sizes 
    % equal [1,1], convert numbers and char-cells to strings.
    %
    % Note that any other cells-within-the-cell will produce errors
    % or wrong results.
    elseif iscell(cell_array{i,j})
        if size(cell_array{i,j},1) == 1 && size(cell_array{i,j},1) == 1
            if isnumeric(cell_array{i,j}{1,1})
                output{i,j} = num2str(cell_array{i,j}{1,1}(1,1));
            elseif ischar(cell_array{i,j}{1,1})
                 output{i,j} = cell_array{i,j}{1,1};
            end;
        end;
        
     % If the cell already contains a string, nothing has to be done.
     elseif ischar(cell_array{i,j})
         output{i,j} = cell_array{i,j};
     end;
     
     % Cell i,j is written to the output file. A delimiter is appended
     % for all but the last element of each row.
     fprintf(output_file,'%s',output{i,j});
     if j ~= size(cell_array,2)
         fprintf(output_file,'%s',delimiter);
     end
end;
% At the end of a row, a newline is written to the output file.
fprintf(output_file,'\r\n');
end;

%% Close output file.    
fclose(output_file);

end