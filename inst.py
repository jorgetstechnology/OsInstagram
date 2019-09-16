import requests
import argparse
import json
import time
import os


def parser():
    parser = argparse.ArgumentParser(prog='OSINT Inst')

    parser.add_argument("-n", "--nickname", help="Nickname?", dest="nickname")

    args = vars(parser.parse_args())
    main(args["nickname"])


def main(nickname):
    url = "https://www.instagram.com/"+nickname
    response = requests.get(url + "?__a=1")

    if "Page Not Found" in response.text:
        print("Page Not Found")
        exit()

    todos = json.loads(response.text)
    os.mkdir("Instagram")
    parse_page(todos)
    photoes(todos["graphql"]["user"])

#getting links of the posts
def get_req_photo(media_to_parse, media, checker, json_media, idprofile_inst):
    media_to_parse += str(media)

    if checker:
        end_cursor = json_media["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]

        data_for_get_req = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a' \
                           '&variables=%7B%22id%22%3A%22' + idprofile_inst + \
                           '%22%2C%22first%22%3A50%2C%22after%22%3A%22' + end_cursor.split("==")[0] + '%3D%3D%22%7D'

        gett = requests.get(data_for_get_req)
        json_media = json.loads(gett.text)
        checker = json_media["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["has_next_page"]
        media = json_media["data"]["user"]["edge_owner_to_timeline_media"]["edges"]

        get_req_photo(media_to_parse, media, checker, json_media["data"]["user"], idprofile_inst)
    else:
        print("Got ", len(str(media_to_parse).split("'shortcode': '")), " post(s)")
        for i in range(1, len(str(media_to_parse).split("'shortcode': '"))):
            link_to_page = str(media_to_parse).split("'shortcode': '")[i].split("',")[0]
            req = requests.get("https://instagram.com/p/" + link_to_page + "/?__a=1")
            json_page = json.loads(req.text)
            parse_media(json_page["graphql"]["shortcode_media"], i)
        print("Done")


def photoes(json_media):
    media = json_media["edge_owner_to_timeline_media"]["edges"]
    checker = json_media["edge_owner_to_timeline_media"]["page_info"]["has_next_page"]
    idprofile_inst = json_media["id"]

    get_req_photo('', media, checker, json_media, idprofile_inst)

#getting infos about account
def parse_page(todos):
    print("Getting info about profile...")
    follow_inst = str(todos["graphql"]["user"]["edge_follow"]["count"])
    followed_by_inst = str(todos["graphql"]["user"]["edge_followed_by"]["count"])
    content_inst = str(todos["graphql"]["user"]["edge_owner_to_timeline_media"]["count"])
    biography = todos["graphql"]["user"]["biography"]
    name = todos["graphql"]["user"]["full_name"]
    username = todos["graphql"]["user"]["username"]
    verified = str(todos["graphql"]["user"]["is_verified"])
    fb = str(todos["graphql"]["user"]["connected_fb_page"])
    business = str(todos["graphql"]["user"]["is_business_account"])

    try:
        link = "\nLink: "+ todos["graphql"]["user"]["external_link"]
    except:
        link = ''


    file = open("Instagram/info.txt", "w", encoding="utf-8")
    info = "Name: "+name+"\nUsername: "+username+"\nBiography: "+biography+"\n\nVerified: "+verified+"\nFollow: "+follow_inst+"\nFollowed: "+\
           followed_by_inst+"\nNumber of posts: "+content_inst+link+"\nBusiness account: "+business+\
           '\nConnected to facebook: '+fb

    file.write(info)
    file.close()


#functions for comments
def get_req_com(shortcode, comments, page_info, list_of_comments, m):
    list_of_comments += str(comments)
    if page_info["has_next_page"]:
        end_cursor = page_info["end_cursor"]
        data_for_get_req = 'https://www.instagram.com/graphql/query/?query_hash=f0986789a5c5d17c2400faebf16efd0d' \
                           '&variables=%7B%22shortcode%22%3A%22' + shortcode + '%22%2C%22first%22%3A50' \
                                            '%2C%22after%22%3A%22' + end_cursor.split("==")[0] + '%3D%3D%22%7D'
        get = requests.get(data_for_get_req)
        json_media = json.loads(get.text)
        try:
            comments = json_media["data"]["shortcode_media"]["edge_media_to_comment"]["edges"]
            page_info = json_media["data"]["shortcode_media"]["edge_media_to_comment"]["page_info"]
            get_req_com(shortcode, comments, page_info, list_of_comments, m)
        except Exception as e:
            if json_media['message'] == "rate limited":
                print("Rate limit. Please wait... (8 min.)")
                time.sleep(480)
                get_req_com(shortcode, comments, page_info, list_of_comments, m)
            else:
                print("Error:","\n",e,json_media)
                pass
    else:
        comments = parse_comm(list_of_comments)
        file = open("Instagram/post " + str(m) + "/comments.txt", "w", encoding="utf-8")
        file.write(comments)
        file.close()

        with open("Instagram/all_comments.txt", "a", encoding="utf-8") as file_all_comments:
            file_all_comments.write(comments)


def parse_comm(list_of_comments):
    list = ''
    num = str(list_of_comments).split("'node':")

    for i in range(1, len(num)):
        if str(num[i]).split("'edge_liked_by': {'count': ")[1].split("}")[0] == '0':
            likes = ''
        else:
            likes = "\t" + str(num[i]).split("'edge_liked_by': {'count': ")[1].split("}")[0] + " like(s)"
        username = "\n" + str(num[i]).split("'username': '")[1].split("'},")[0]
        try:
            text = str(num[i]).split("'text': '")[1].split("'")[0] + "'"
        except:
            text = str(num[i]).split(''''text': "''')[1].split('"')[0] + "'"
        list += username + "  '" + text +likes+"\n"

    return list


def comm(json_page, m):
    list_of_comments = ''
    try:
        try:
            comments = json_page["edge_media_to_parent_comment"]["edges"]
            page_info = json_page["edge_media_to_parent_comment"]["page_info"]
        except KeyError:
            comments = json_page["edge_media_to_comment"]["edges"]
            page_info = json_page["edge_media_to_comment"]["page_info"]
    except Exception as e:
        print("\n\n", json_page,"\nError:", e)
        exit()
    get_req_com(json_page["shortcode"], comments, page_info, '', m)

#saving infos and photoes from account
def parse_media(json_page, m):

    view_count = ''
    os.mkdir("Instagram/post " + str(m))
    captions = '\nCaption(s): '
    print("Downloading post " + str(m))
    if json_page["__typename"] == "GraphVideo":
        view_count = str("\nView count = " + str(json_page["video_view_count"]))
        out = open("Instagram/post " + str(m) + "/video.txt", "w")
        out.write(str("https://instagram.com/p/"+json_page["shortcode"]))
        out.close()

    if json_page["__typename"] == "GraphImage":
        photo = str(json_page["display_resources"][-1]["src"])
        p = requests.get(photo)
        out = open("Instagram/post " + str(m) + "/img" + str(m) + ".jpg", "wb")
        out.write(p.content)
        out.close()
        captions = "\n"+json_page["accessibility_caption"]

    if json_page["__typename"] == "GraphSidecar":
        for i in range(len(json_page["edge_sidecar_to_children"]["edges"])):
            photoes = json_page["edge_sidecar_to_children"]["edges"][i]["node"]["display_resources"][-1]["src"]
            p = requests.get(photoes)
            out = open("Instagram/post "+str(m)+"/img"+str(i)+".jpg", "wb")
            out.write(p.content)
            out.close()
            try:
                captions += "\nphoto №"+str(i)+"-"+ str(json_page["edge_sidecar_to_children"]["edges"][i]
                                                  ["node"]["accessibility_caption"])+"\n"
            except:
                view_count = str("\nView count = " + str(json_page["edge_sidecar_to_children"]["edges"][i]
                                                  ["node"]["video_view_count"]))
                out = open("Instagram/post " + str(m) + "/video.txt", "w")
                out.write(str("https://instagram.com/p/" + json_page["shortcode"]))
                out.close()

    likes = "\nlikes: " + str(json_page["edge_media_preview_like"]["count"])+"\n"
    link = "Link - "+"instagram.com/p/"+json_page["shortcode"]+"\n"
    location = json_page["location"]

    if location is not None:
        with open("Instagram/all_locations.txt", "a", encoding="utf-8") as file:
            file.write("post "+str(m)+"\n"+str(location)+"\n")
    else:
        location = ''
        pass


    if json_page["edge_media_to_tagged_user"]["edges"] == []:
        tagged_user = ''
    else:
        tagged = str(json_page["edge_media_to_tagged_user"]).split("node")
        tagged_user = '\nTagged user(s): '
        for i in range(1, len(tagged)):
             tagged_user += "@"+str(json_page["edge_media_to_tagged_user"]).split("username': '")[i].split("'}")[0]+\
                    " ("+str(json_page["edge_media_to_tagged_user"]).split("full_name': '")[i].split("', ")[0]+")\n"
        with open("Instagram/all_tagged.txt", "a", encoding="utf-8") as file:
            file.write(str("post " + str(m) + ":" + tagged_user + "\n"))


    file = open("Instagram/post "+str(m)+"/info.txt", "w", encoding="utf-8")

    try:
        text = "text: '"+str(json_page["edge_media_to_caption"]["edges"][0]["node"]["text"])+"'\n"
    except:
        text = "text: None\n"

    all_information = str(text+likes+tagged_user+"\nLocation: "+str(location)+captions+view_count+"\n"+link)
    file.write(all_information)
    file.close()

    try:
        checker_for_comment = json_page["edge_media_to_parent_comment"]["count"]
    except:
        checker_for_comment = json_page["edge_media_to_comment"]["count"]

    if checker_for_comment != 0:
        comm(json_page, m)
    else:
        pass


if __name__ == '__main__':
    parser()
