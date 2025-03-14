#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <libxml/HTMLparser.h>
#include <libxml/xpath.h>
#include <sys/stat.h>
#include <unistd.h>

#define MAX_LINKS 1000
#define MAX_LINK_LENGTH 256
#define URL "https://inventory.raw.pm/tools.html"

struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if (!ptr) return 0;

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

void clone_repository(const char *link) {
    char command[512];
    snprintf(command, sizeof(command), "git clone %s repos/%s", link, strrchr(link, '/') + 1);
    int result = system(command);
    if (result == 0) {
        printf("Successfully cloned %s\n", link);
    } else {
        printf("Failed to clone %s\n", link);
    }
}

int main(void) {
    CURL *curl_handle;
    CURLcode res;
    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;

    curl_global_init(CURL_GLOBAL_ALL);
    curl_handle = curl_easy_init();

    curl_easy_setopt(curl_handle, CURLOPT_URL, URL);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, "libcurl-agent/1.0");

    res = curl_easy_perform(curl_handle);

    if (res != CURLE_OK) {
        fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
    } else {
        htmlDocPtr doc = htmlReadMemory(chunk.memory, chunk.size, URL, NULL, 0);
        if (doc == NULL) {
            fprintf(stderr, "Failed to parse HTML\n");
            return 1;
        }

        xmlXPathContextPtr context = xmlXPathNewContext(doc);
        xmlXPathObjectPtr result = xmlXPathEvalExpression((xmlChar*)"//a[@href]", context);

        if (result == NULL) {
            fprintf(stderr, "Failed to evaluate XPath expression\n");
            return 1;
        }

        char github_links[MAX_LINKS][MAX_LINK_LENGTH];
        int link_count = 0;

        for (int i = 0; i < result->nodesetval->nodeNr && link_count < MAX_LINKS; i++) {
            xmlNodePtr node = result->nodesetval->nodeTab[i];
            xmlChar* href = xmlGetProp(node, (xmlChar*)"href");
            if (strstr((char*)href, "github.com")) {
                strncpy(github_links[link_count], (char*)href, MAX_LINK_LENGTH - 1);
                github_links[link_count][MAX_LINK_LENGTH - 1] = '\0';
                if (strstr(github_links[link_count], ".git") == NULL) {
                    strncat(github_links[link_count], ".git", MAX_LINK_LENGTH - strlen(github_links[link_count]) - 1);
                }
                link_count++;
            }
            xmlFree(href);
        }

        xmlXPathFreeObject(result);
        xmlXPathFreeContext(context);
        xmlFreeDoc(doc);

        if (link_count == 0) {
            printf("Warning: No GitHub links found on the page.\n");
        } else {
            FILE *file = fopen("github_links.txt", "w");
            if (file == NULL) {
                fprintf(stderr, "Failed to open file for writing\n");
                return 1;
            }

            mkdir("repos", 0777);

            for (int i = 0; i < link_count; i++) {
                fprintf(file, "%s\n", github_links[i]);
                clone_repository(github_links[i]);
            }

            fclose(file);
            printf("GitHub links have been saved to github_links.txt and cloning attempted.\n");
        }
    }

    curl_easy_cleanup(curl_handle);
    free(chunk.memory);
    curl_global_cleanup();

    return 0;
}
