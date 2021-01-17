window.onload = get_channels

        async function fetchWithTimeout(resource, options) {
            const {timeout = 120000} = options;

            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);

            const response = await fetch(resource, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(id);

            return response;
        }

        function toggle(source) {
            checkboxes = document.getElementsByName('chan-checkbox');
            for (var i = 0, n = checkboxes.length; i < n; i++) {
                checkboxes[i].checked = source.checked;
            }
        }

        function remove_channel(source) {
            checkboxes = document.getElementsByName("chan-checkbox");
            var channels = [];
            for (var i = 0, n = checkboxes.length; i < n; i++) {
                if (checkboxes[i].checked) {
                    channels.push(checkboxes[i].id)
                }
            }
            if (channels.length > 0) {
                $(source).prop("disabled", true);

                console.log(channels)
                fetchWithTimeout(`${window.origin}/api/remove-channel`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(channels),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(function (response) {
                    console.log(response.status);
                    if (response.ok) {
                        $("#remove").modal("hide");
                        $(source).html(`Submit`);
                        $(source).prop("disabled", false);
                        get_channels();
                    }
                });

            } else alert("No channels selected");

        }

        function add_channel(source) {
            var url = document.getElementById("chan-url");
            var dlvideo = document.getElementById("video-download");
            var dlstream = document.getElementById("stream-download");
            var data = {
                url: url.value,
                dlvideo: dlvideo.checked,
                dlstream: dlstream.checked
            };
            if (url.value) {
                $(source).prop("disabled", true);
                $(source).html(
                    `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...`
                );
                fetchWithTimeout(`${window.origin}/api/add-channel`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(data),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(function (response) {
                    console.log(response.status);
                    $(source).html(`Submit`);
                    if (response.ok) {
                        $("#add").modal("hide");
                        $(source).prop("disabled", false);
                        get_channels();
                    }
                });
            } else alert("URL can't be empty!");

        }

        function check_video(source) {
            var vidid = document.getElementById("video-id"),
                msgon = document.getElementById("availability-online"),
                msgof = document.getElementById("availability-offline");
            var data = {
                vidid: vidid.value,
            };
            if (vidid.value) {
                $(source).prop("disabled", true);

                fetchWithTimeout(`${window.origin}/api/check-availability`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(data),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(response => response.json())
                    .then(function (res) {
                    console.log(res);
                    $(source).prop("disabled", false);
                    let online = res["online"]
                        offline = res["offline"];
                    if (online === true){
                        msgon.innerText = vidid.value +" is available online"
                    }
                    else {
                        msgon.innerText = vidid.value +" is not available online"
                    }
                    if (offline === true){
                        msgof.innerText = vidid.value +" is available offline"
                    }
                    else {
                        msgof.innerText = vidid.value +" is not available offline"
                    }


                })
            }
        }

        function add_video(source,force=null){
            var vidid = document.getElementById("video-id");
            var data = {
                vidid: vidid.value,
                force: force
            };
            if (vidid.value) {
                $(source).prop("disabled", true);
                fetchWithTimeout(`${window.origin}/api/add-video`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(data),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(function (response) {
                    console.log(response.json());
                    $(source).prop("disabled", false);
                });
            }
        }

        function redownload(source,force=null){
            var vidid = document.getElementById("video-id");
            var data = {
                vidid: vidid.value,
            };
            if (vidid.value) {
                $(source).prop("disabled", true);
                fetchWithTimeout(`${window.origin}/api/check-availability`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(data),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(response => response.json())
                    .then(function (res) {
                        if (res["online"] === false) {
                            if (confirm("Video is not available online. Do you want to proceed?") === false) {
                                return
                            }
                        }
                        data = {
                            vidid:vidid.value,
                            fs: true
                        }
                        fetchWithTimeout(`${window.origin}/api/remove-video`, {
                        method: "POST",
                        credentials: "include",
                        body: JSON.stringify(data),
                        cache: "no-cache",
                        headers: new Headers({
                            "content-type": "application/json"
                        })
                    }).then(function (response) {
                        console.log(response.json());
                        $(source).prop("disabled", false);
                        data = {
                            vidid:vidid.value,
                            force: false
                        }
                        fetchWithTimeout(`${window.origin}/api/add-video`, {
                            method: "POST",
                            credentials: "include",
                            body: JSON.stringify(data),
                            cache: "no-cache",
                            headers: new Headers({
                                "content-type": "application/json"
                            })
                        })
                            $(source).prop("disabled", false);

                    })



                });

            }
        }

        function remove_video(source,fs=null){
            var vidid = document.getElementById("video-id");
            var data = {
                vidid: vidid.value,
                fs: fs
            };
            if (vidid.value) {
                $(source).prop("disabled", true);
                fetchWithTimeout(`${window.origin}/api/remove-video`, {
                    method: "POST",
                    credentials: "include",
                    body: JSON.stringify(data),
                    cache: "no-cache",
                    headers: new Headers({
                        "content-type": "application/json"
                    })
                }).then(function (response) {
                    console.log(response.json());
                    $(source).prop("disabled", false);
                });
            }
        }

        function get_channels() {
            var table = document.getElementById("channel-table");
            let channels = [];
            fetchWithTimeout(`${window.origin}/api/get-channels`, {
                method: "GET",
                credentials: "include",
                cache: "no-cache",
                headers: new Headers({
                    "content-type": "application/json"
                })
            })
                .then(response => response.json())
                .then(function (channels) {
                    console.log(channels)
                    $("#channel-table tr").remove();
                    if (channels.length > 0) {
                        for (let i = 0, n = channels.length; i < n; i++) {
                            let dict = channels[i],
                                row = table.insertRow(i),
                                number = row.insertCell(0),
                                name = row.insertCell(1),
                                url = row.insertCell(2),
                                dlvideos = row.insertCell(3),
                                dlstreams = row.insertCell(4);

                            number.outerHTML = "<th scope=\"row\">\n" +
                                "<label class=\"form-check-label\">\n" +
                                (i + 1) + " <input name=\"chan-checkbox\" type=\"checkbox\" \n" +
                                "id=\"" + dict["id"] + "\">\n" +
                                "</label>\n" +
                                " </th>";
                            name.outerHTML = "<td>" + dict["name"] + "</td>";
                            url.outerHTML = "<td><a href=\"" + (dict["url"]) + "\" target=\"_blank\">" + dict["url"] + "</a></td>";
                            if (dict["downloadvideos"] === "True") {
                                dlvideos.outerHTML = "<td><div style=\"margin-top: auto;margin-bottom: auto;text-align: center;\">" +
                                    "<label class=\"form-check-label\">\n" +
                                    "<input type=\"checkbox\" checked disabled>\n" +
                                    "</label>" +
                                    "</div></td>";
                            } else {
                                dlvideos.outerHTML = "<td><div style=\"margin-top: auto;margin-bottom: auto;text-align: center;\">" +
                                    "<label class=\"form-check-label\">\n" +
                                    "<input type=\"checkbox\"  disabled>\n" +
                                    "</label>" +
                                    "</div></td>";
                            }
                            if (dict["downloadstreams"] === "True") {
                                dlstreams.outerHTML = "<td><div style=\"margin-top: auto;margin-bottom: auto;text-align: center;\">" +
                                    "<label class=\"form-check-label\">\n" +
                                    "<input type=\"checkbox\" checked disabled>\n" +
                                    "</label>" +
                                    "</div></td>";
                            } else {
                                dlstreams.outerHTML = "<td><div style=\"margin-top: auto;margin-bottom: auto;text-align: center;\">" +
                                    "<label class=\"form-check-label\">\n" +
                                    "<input type=\"checkbox\"  disabled>\n" +
                                    "</label>" +
                                    "</div></td>";
                            }
                        }
                    } else {
                        let tablerow = table.insertRow(0),
                            cell = tablerow.insertCell(0);
                        cell.outerHTML = "<td style=\"text-align: center\" colspan=\"5\">Could not find any records.</td>";
                    }
                });

        }