# Ignoring all warnings
from warnings import filterwarnings
filterwarnings('ignore')

# Importing Libraries
from os import system
system('cls')

import urllib3, re, os, cv2
from tqdm import tqdm
from shutil import rmtree
from PIL import Image

system('cls')
print('Libraries Imported')

# Generate manga url from manga title
def create_manga_url(manga_title, number, with_for = False):
    manga_title = '_'.join(manga_title.lower().split(' '))
    if with_for:
        manga_url = "https://manganelo.com/manga/read_" + manga_title + "_manga_online_for_free" + str(number)
    else:
        manga_url = "https://manganelo.com/manga/read_" + manga_title + "_manga_online_free" + str(number)
    return manga_url

# Generate HTML file of given name from a given url
def generate_html(url):
    http = urllib3.PoolManager()
    r = http.request('GET', url)
    r.release_conn()
    return str(r.data)

# Write HTML content to a file
def write_html_content(html_content, filename):
    os.mkdir("./Data")
    f_write = open("./Data/" + filename, "w")
    f_write.write(html_content)
    f_write.close()
    return "./Data/" + filename

# Return content of an HTML file as string
def read_html_content(location):
    f_open = open(location, "r")
    html_content = str(f_open.read())
    f_open.close()
    return html_content

# Verify whether a page is a valid manga page or not
def verify_manga_page(html_content):
    chapters = html_content.count("Chapter")
    return False if chapters == 0 else True

# Generate Lines from HTML content
def generate_lines(html_content):
    lines = html_content.split('\n')
    return lines

# Generate Content of Manga Page
def generate_manga_page_content(manga_title):
    is_verified = False
    for number in range(10):
        number += 1
        print("Trying with number " + str(number) + " ....")
        manga_page_url = create_manga_url(manga_title, number)
        html_content = generate_html(manga_page_url)
        is_verified = verify_manga_page(html_content)
        if is_verified:
            return html_content.split('\\n')
        manga_page_url = create_manga_url(manga_title, number, with_for = True)
        html_content = generate_html(manga_page_url)
        is_verified = verify_manga_page(html_content)
        if is_verified:
            return html_content.split('\\n')
    return None

# Save HTML Content to a file
def save_html_content(html_content, filename):
    try:
        rmtree("./Data")
    except:
        pass
    os.mkdir("./Data")
    f_write = open("./Data/" + filename, "w")
    f_write.write(html_content)
    f_write.close()

# Generate list of HTML lines from a file
def generate_lines_from_html(location):
    f_open = open(location, "r")
    string = str(f_open.read())
    f_open.close()
    return string.split('\\n')

def get_chapter_urls(manga_page_content):
    c = 0
    urls = []
    print("Generating Chapter Urls")
    for line in tqdm(manga_page_content):
        if len(re.findall(r'Chapter [0-9]*\.*[0-9]*', line)) != 0:
            url = re.findall(r'a href="([^"]*)"', line)
            url = url[0] if len(url) > 0 else ""
            if url.count("chapter") > 0:
                urls.append(url)
    return urls

def generate_image_sources(html_content_lines):
    img_sources = []
    for line in html_content_lines:
        contents = re.findall(r'img src="([^"]*)"', line)
        for content in contents:
            if len(re.findall(r'[0-9]*\.jpg', content)) > 0:
                img_sources.append(content)
    return img_sources 

# Download an Image from an URL and save it in a location
def save_image(url, location):
    http = urllib3.PoolManager()
    r = http.request('GET', url, preload_content = False)
    with open(location, 'wb') as out:
        while True:
            data = r.read(32)
            if not data:
                break
            out.write(data)
    r.release_conn()

# Save Images from each Chapter
def save_images_in_chapter(img_sources, chapter_name):
    os.mkdir('./Data/' + chapter_name)
    c = 1
    print('Downloading Images for ' + chapter_name + ' ....')
    for source in tqdm(img_sources):
        save_image(source, "./Data/" + chapter_name + "/" + str(c) + ".jpg")
        c += 1

# Save Images as pdf
def save_as_pdf(chapter_name):
    location = "./Data/" + chapter_name + "/"
    filenames = sorted([int(filename[:-4]) for filename in os.listdir(location)])
    filenames = [str(filename) + ".jpg" for filename in filenames]
    image_list = []
    for filename in filenames:
        try:
            image_list.append(Image.open(location + filename))
        except:
            pass
    pdf_filename = "./Data/" + chapter_name + ".pdf"
    image_list[0].save(pdf_filename, "PDF" , resolution = 100.0, save_all = True, append_images = image_list)

# Preprocess Images
def preprocess_images(chapter_name):
    filenames = os.listdir("./Data/" + chapter_name)
    print("Preprocessing Images from " + chapter_name + " ....")
    for file in tqdm(filenames):
        image = cv2.imread("./Data/" + chapter_name + "/" + file)
        os.remove("./Data/" + chapter_name + "/" + file)
        cv2.imwrite("./Data/" + chapter_name + "/" + file, image)


# main function
def main():
    manga_title = input('Enter title of the manga: ')
    os.mkdir("./Data/")
    manga_page_content = generate_manga_page_content(manga_title)
    if manga_page_content != None:
        print("Number of lines in Manga Page Content:", len(manga_page_content))
        chapter_urls = get_chapter_urls(manga_page_content)
        print("Downloading Images ....")
        for chapter_url in chapter_urls[::-1]:
            if chapter_url.count('_'.join(manga_title.lower().split(' '))) > 0:
                image_sources = generate_image_sources(generate_html(chapter_url).split('\\n'))
                chapter_name = chapter_url.split("/")[-1]
                save_images_in_chapter(image_sources, chapter_name)
                preprocess_images(chapter_name)
                save_as_pdf(chapter_name)

# Driver Code
main()
