async function fetchWithTimeout(resource, options) {
            const {timeout = 8000} = options;

            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(resource, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(id);

            return response;
        }

        function AddStreams(item, index) {
            let element = document.createElement("li"),
                a = document.createElement("a"),
                list = document.getElementById("a-streams-list");
            a.textContent = item;
            a.setAttribute("class", "card-link text-white")
            a.setAttribute("href", item);
            a.setAttribute("target", "_blank");
            element.appendChild(a);
            list.appendChild(element);
        }

        function AddVideos(item, index) {
            let element = document.createElement("li"),
                a = document.createElement("a")
            list = document.getElementById("a-videos-list");
            a.textContent = item;
            a.setAttribute("class", "card-link text-white")
            a.setAttribute("href", "https://www.youtube.com/watch?v=" + item);
            a.setAttribute("target", "_blank");
            element.appendChild(a);
            list.appendChild(element);
        }

        function get_status() {
            fetchWithTimeout(`${window.origin}/api/get-status`, {
                method: "GET",
                credentials: "include",
                cache: "no-cache",
                headers: new Headers({
                    "content-type": "application/json"
                })
            })
                .then(response => response.json())
                .then(function (status) {
                    let a_streams = status["a_streams"],
                        a_videos = status["a_videos"];
                    $("#a-streams-list li").remove();
                    $("#a-videos-list li").remove();
                    console.log(status);
                    a_streams.forEach(AddStreams);
                    a_videos.forEach(AddVideos);

                    let a_streams_count = document.getElementById("a-streams-count"),
                        a_videos_count = document.getElementById("a-videos-count"),
                        chan_count = document.getElementById("chan_count"),
                        vid_count = document.getElementById("vid_count"),
                        a_fetchers = document.getElementById("a_fetchers");

                    a_streams_count.innerText = a_streams.length;
                    a_videos_count.innerText = a_videos.length;
                    chan_count.innerText = status["chan_count"];
                    vid_count.innerText = status["down_count"];
                    a_fetchers.innerText = status["a_fetchers"];
                    if (status["dl_streams"] === "True") {
                        document.getElementById("astreams-card").className = "card text-white bg-success mb-3 scroll";
                    } else if (status["dl_streams"] === "False") {
                        document.getElementById("astreams-card").className = "card text-white bg-danger mb-3 scroll";
                    } else {
                        document.getElementById("astreams-card").className = "card text-white bg-secondary mb-3 scroll";
                    }
                    if (status["dl_videos"] === "True") {
                        document.getElementById("avideos-card").className = "card text-white bg-success mb-3 scroll";
                    } else if (status["dl_videos"] === "False") {
                        document.getElementById("avideos-card").className = "card text-white bg-danger mb-3 scroll";
                    } else {
                        document.getElementById("avideos-card").className = "card text-white bg-secondary mb-3 scroll";
                    }

                });

        }

        window.onload = get_status
        window.setInterval(get_status, 5000)