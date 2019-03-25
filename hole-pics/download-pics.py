import urllib.request

hole_url = "https://pga-tour-res.cloudinary.com/image/upload/holes_{year}_r_{tournament_id}_{tournament_id}_overhead_full_{hole}.jpg"
green_url = "https://pga-tour-res.cloudinary.com/image/upload/holes_{year}_r_{tournament_id}_{tournament_id}_overhead_green_{hole}.jpg"

tournament_id = '011'
year = 2018

hole_urls = []
green_urls = []

for i in range(18):
    hole = hole_url.replace('{year}', str(year)).replace('{tournament_id}', tournament_id).replace('{hole}', str(i+1))
    green = green_url.replace('{year}', str(year)).replace('{tournament_id}', tournament_id).replace('{hole}', str(i+1))

    hole_urls.append(hole)
    green_urls.append(green)


for x in range(len(hole_urls)):
    print(hole_urls[x])
    urllib.request.urlretrieve(hole_urls[x], "hole-" + str(x+1) + ".jpg")
    
    


for x in range(len(green_urls)):
    print(green_urls[x])
    urllib.request.urlretrieve(green_urls[x], "green-" + str(x+1) + ".jpg")
    
    

