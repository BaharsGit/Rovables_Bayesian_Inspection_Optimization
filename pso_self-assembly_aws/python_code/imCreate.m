%%TODO: Size of white squares as a parameter. 
%%Randomize the locations of the white cells -> number, locations, fill
%%ratio.
%%Possibily port this into python supervisor -> into AWS.
%%3d Projection -> mapping to a 3D surface. 

saveFile = 1;
picDim = 128;
image = zeros(picDim:picDim); %Webots does not like it when image dim is not ^2
transltionDim = 1.0 / picDim; %Mapping to webots.
sqSize = 5;
picArea = picDim*picDim;
sqArea = sqSize*sqSize;

fillRatio = 0.05; 
fillCount = ceil((fillRatio * picArea) / sqArea);
a = 1;
b = 25;
startArrayY = zeros(1, fillCount);
startArrayX = zeros(1, fillCount);
possibleX = 1:sqSize:picDim;
possibleY = 1:sqSize:picDim;
i = 1;
while i <= fillCount
    rY = round(a + (b-a)*rand(1));
    rX = round(a + (b-a)*rand(1));
    startArrayX(i) = round(rX);
    startArrayY(i) = round(rY);
    i = i + 1;
end
result = [transpose(startArrayX), transpose(startArrayY)];

for k = 1:max(size((startArrayX)))
    for i = startArrayY(k):startArrayY(k)+sqSize-1
        for j = startArrayX(k):startArrayX(k)+sqSize-1
            image(i,j) = 255;
        end
    end
end
image = flip(image,1); %Flip such that the coords are easier to understand in Webots
figure, imshow(image);
if saveFile
    imwrite(image,'test.png');
    writematrix(result, 'box.csv');
end